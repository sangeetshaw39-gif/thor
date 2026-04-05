import cv2
import mediapipe as mp
import threading
import time
import copy
import numpy as np

class HandTracker:
    def __init__(self, camera_index=0, width=640, height=480):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = cv2.VideoCapture(self.camera_index)
        
        # Optimize capture format if possible
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.mp_selfie = mp.solutions.selfie_segmentation
        # model_selection=1 is Landscape mode: heavily optimized for speed, perfect for Intel i3
        self.segmenter = self.mp_selfie.SelfieSegmentation(model_selection=1)
        
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True, # Critical for accurate iris/eye tracking
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Shared data
        self.lock = threading.Lock()
        self.latest_frame = None
        self.latest_landmarks = None
        self.latest_face_landmarks = None # NEW: Face tracking
        self.latest_mask = None
        self.latest_state = 'Idle' # 'Idle', 'Point', 'Aura'
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _determine_state(self, hand_landmarks):
        # A simple heuristical approach for states using y-coords (lower y = higher up in image)
        # 5,9,13,17 are the base joints of fingers
        # 8, 12, 16, 20 are the tips

        def is_extended(tip, base):
            return hand_landmarks.landmark[tip].y < hand_landmarks.landmark[base].y

        index_ext = is_extended(8, 5)
        middle_ext = is_extended(12, 9)
        ring_ext = is_extended(16, 13)
        pinky_ext = is_extended(20, 17)
        
        thumb_ext = hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x if hand_landmarks.landmark[5].x < hand_landmarks.landmark[17].x else hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x # Rough thumb heuristic

        open_fingers = sum([index_ext, middle_ext, ring_ext, pinky_ext, thumb_ext])
        
        if index_ext and not middle_ext and not ring_ext and not pinky_ext:
            return 'Point'
        elif open_fingers >= 4:
            return 'Aura'
        else:
            return 'Idle'

    def _run(self):
        while self.running:
            success, frame = self.cap.read()
            if not success:
                time.sleep(0.01)
                continue
            
            # Flip frame horizontally for a selfie-view display
            frame = cv2.flip(frame, 1)
            # Convert BGR to RGB for MediaPipe
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_rgb.flags.writeable = False
            
            # Run all massive ML models concurrently
            results = self.hands.process(image_rgb)
            seg_results = self.segmenter.process(image_rgb)
            face_results = self.face_mesh.process(image_rgb)
            
            mask = None
            if seg_results.segmentation_mask is not None:
                mask = (seg_results.segmentation_mask * 255).astype(np.uint8)
            
            state = 'Idle'
            landmarks_list = None
            face_landmarks_list = None
            
            if face_results.multi_face_landmarks:
                face = face_results.multi_face_landmarks[0]
                face_landmarks_list = [(lm.x, lm.y) for lm in face.landmark]
            
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                state = self._determine_state(hand_landmarks)
                landmarks_list = [(lm.x, lm.y) for lm in hand_landmarks.landmark]
            
            with self.lock:
                self.latest_frame = frame
                self.latest_landmarks = landmarks_list
                self.latest_face_landmarks = face_landmarks_list
                self.latest_state = state
                self.latest_mask = mask

    def get_latest(self):
        with self.lock:
            if self.latest_frame is None:
                return None, None, 'Idle', None, None
            # Returning 5 elements now: frame, hand_landmarks, state, mask, face_landmarks
            return self.latest_frame.copy(), copy.copy(self.latest_landmarks), self.latest_state, self.latest_mask, copy.copy(self.latest_face_landmarks)

    def stop(self):
        self.running = False
        self.thread.join()
        self.cap.release()
