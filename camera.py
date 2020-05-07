import face_recognition
import cv2
import numpy as np
import glob
import os
import logging
import datetime
import pickle

class VideoCamera(object):
    
    def __init__(self, args):
        #self.IMAGES_PATH = args.imagespath  # put your reference images in here
        #self.IMAGES_UNKNOW = args.imagesunknow

        #CAMERA_DEVICE_ID = ("rtsp://name:9107@192.168.0.11:554/cam/realmonitor?channel=3&subtype=0")    
        if args.remote:    
            self.CAMERA_DEVICE_ID = ("http://192.168.3.165:8080/video.cgi?.mjpg")
        else:
            self.CAMERA_DEVICE_ID = (0)
        self.MAX_DISTANCE = float(args.maxdistance)  # increase to make recognition less strict, decrease to make more strict

        self.database = self.setup_database()

        # the face_recognitino library uses keys and values of your database separately
        self.known_face_encodings = list(self.database.values())
        self.known_face_names = list(self.database.keys())

        # Open a handler for the camera
        self.video_capture = cv2.VideoCapture(self.CAMERA_DEVICE_ID)


    def get_face_embeddings_from_image(self, image, convert_to_rgb=False):
        """
        Take a raw image and run both the face detection and face embedding model on it
        """
        # Convert from BGR to RGB if needed
        if convert_to_rgb:
            image = image[:, :, ::-1]

        # run the face detection model to find face locations
        #face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=1, model="cnn")
        face_locations = face_recognition.face_locations(image)

        # run the embedding model to get face embeddings for the supplied locations
        face_encodings = face_recognition.face_encodings(image, face_locations)

        return face_locations, face_encodings


    def setup_database(self):
        """
        Load reference images and create a database of their face encodings
        """
        # database = {}

        # for filename in glob.glob(os.path.join(self.IMAGES_PATH, '*.jpg')):
        #     # load image
        #     image_rgb = face_recognition.load_image_file(filename)

        #     # use the name in the filename as the identity key
        #     identity = os.path.splitext(os.path.basename(filename))[0]

        #     # get the face encoding and link it to the identity
        #     locations, encodings = self.get_face_embeddings_from_image(image_rgb)
        #     database[identity] = encodings[0]
        #     # logging.info("Database read.")

        # return database
        database = {}

        if os.stat('teste.dat').st_size > 0:
            face_dataset = open('teste.dat','rb')
            database = pickle.load(face_dataset)

        return database


    # def include_in_database(self, filename, name):
    #     image_rgb = face_recognition.load_image_file(filename)

    #     locations, encodings = self.get_face_embeddings_from_image(image_rgb)
    #     if len(locations) > 0 and len(encodings) > 0:
    #         self.database[name] = encodings[0]
    #         return True
    #     else:
    #         return False


    def paint_detected_face_on_image(self, frame, location, name=None, video_capture=None):
        """
        Paint a rectangle around the face and write the name
        """
        # unpack the coordinates from the location tuple
        top, right, bottom, left = location

        if name is None:
            name = 'Unknown'
            color = (0, 0, 255)  # red for unrecognized face
        else:

            color = (0, 255, 255)  # dark green for recognized face

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        # Draw a label with a name below the face
        #cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, name, (left, top - 60), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 255), 2)


    def cropimage(self, frame, location):
        top, right, bottom, left = location
        content = str(top) + ' ' + str(right) + ' ' + str(bottom) + ' ' + str(left)
        #cv2.putText(frame, content, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

        '''        
        x, y, w, h = location
        r = max(w, h) / 2
        centerx = x + w / 2
        centery = y + h / 2
        nx = int(centerx - r)
        ny = int(centery - r)
        nr = int(r * 2)

        crop_img = frame[ny:ny+nr, nx:nx+nr]
        
        crop_img = frame[top:top+left, bottom:bottom+right].copy()
        '''
        #cv2.imwrite(os.path.join(self.IMAGES_UNKNOW, "image%s.jpg" % datetime.datetime.now().strftime('%e_%m_%Y_%H_%M_%S')), frame)    
        return frame


    def run_face_recognition(self, database):
        name = ''
        pic = ''
        # Grab a single frame of video (and check if it went ok)
        ok, frame = self.video_capture.read()
        if not ok:
            logging.error("Could not read frame from camera. Stopping video capture.")


        # run detection and embedding models
        face_locations, face_encodings = self.get_face_embeddings_from_image(frame, convert_to_rgb=True)

        # Loop through each face in this frame of video and see if there's a match
        for location, face_encoding in zip(face_locations, face_encodings):

            # get the distances from this encoding to those of all reference images
            distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)

            # select the closest match (smallest distance) if it's below the threshold value
            if np.any(distances <= self.MAX_DISTANCE):
                best_match_idx = np.argmin(distances)
                name = self.known_face_names[best_match_idx]                
                # put recognition info on the image
                self.paint_detected_face_on_image(frame, location, name)
            else:
                name = None                
                cropped = self.cropimage(frame.copy(), location)                
                if cropped.size > 0:
                    retUnknow, pic = cv2.imencode('.jpg', cropped)                
                #pic = pic.tobytes()

        # Display the resulting image        
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes(), name, pic


    def get_frame(self):
        frame, name, unrecognized = self.run_face_recognition(self.database)
        return frame, name, unrecognized
