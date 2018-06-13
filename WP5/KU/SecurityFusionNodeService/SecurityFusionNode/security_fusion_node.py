# security_fusion_node.py
"""The class that handles the storage of current messages on the sfn_service and contains the functions to process those
messages"""
import numpy as np
import json
import time
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy import and_
from sqlalchemy import create_engine
from pathlib import Path
import requests
import sys
sys.path.append(str(Path(__file__).absolute().parents[3]))
from KU.SharedResources.convert_to_meter import convert_to_meter
from KU.SharedResources.rotate_image import rotate_image

__version__ = '0.1'
__author__ = 'RoViT (KU)'

sfn_base = declarative_base()
log_base = declarative_base()


class Messages(sfn_base):
    __tablename__ = 'messages'
    # Here we define columns for the table messages
    id = Column(String(300), primary_key=True)
    cam_id = Column(String(100), nullable=True)
    module_id = Column(String(300), nullable=False)
    msg = Column(MEDIUMTEXT, nullable=False)


class Configs(sfn_base):
    __tablename__ = 'configs'
    # Here we define columns for the table configs
    conf_id = Column(String(300), primary_key=True)
    msg = Column(MEDIUMTEXT, nullable=False)


class Logs(log_base):
    __tablename__ = 'logs'
    # Here we define columns for the table configs
    job_id = Column(String(100), primary_key=True)
    time = Column(String(100), nullable=False)
    log = Column(String(1000), nullable=False)


class SecurityFusionNode:

    def __init__(self, module_id):
        self.module_id = module_id
        self.module_type = 'crowd_density_global'
        self.last_amalgamation = time.time()
        self.timer = 0
        self.state = 'active'


        # self.sfn_engine = create_engine('sqlite:///sfn_database.db')
        self.sfn_engine = create_engine('mysql://root:root@127.0.0.1:3306/sfn_database')

        sfn_base.metadata.drop_all(self.sfn_engine)
        sfn_base.metadata.create_all(self.sfn_engine)
        sfn_session_factory = sessionmaker(bind=self.sfn_engine)
        self.sfn_db_session = scoped_session(sfn_session_factory)

        # self.log_engine = create_engine('sqlite:///log_database.db')
        self.log_engine = create_engine('mysql://root:root@localhost:3307/log_database')

        log_base.metadata.drop_all(self.log_engine)
        log_base.metadata.create_all(self.log_engine)
        log_factory_session = sessionmaker(bind=self.log_engine)
        self.log_db_session = scoped_session(log_factory_session)

    def get_session(self, log=False):
        if log is False:
            session = self.sfn_db_session()
        else:
            session = self.log_db_session()
        return session

    def insert_db(self, c_id, m_id, msg, session=None):
        """Insert for recent camera messages"""
        if session is None:
            session = self.get_session()

        # MESSAGE SORTING CODE: FIND THE CAMERA ID AND MODULE AND UPDATE recent_cam_messages
        log_text = ''
        # row: the index of previous message for this camera and module
        row = self.query_db(session, c_id, m_id)

        # IF AN ENTRY IS FOUND:
        if row is not None and len(row) != 0:
            log_text = log_text + 'PREVIOUS MESSAGE FROM {}, FROM {}, ALREADY STORED, REPLACING. '.format(m_id, c_id)
            self.delete_db(session, c_id, m_id)  # Delete the previous message from the database
        else:
            # THIS IS THE FIRST INSTANCE OF THIS camera_id AND wp_module PAIR
            log_text = log_text + 'THIS IS A NEW MESSAGE FROM {}, ({}). '.format(m_id, c_id)

        session.add(Messages(id=time.time(), cam_id=c_id, module_id=m_id, msg=msg))
        try:
            session.commit()
        except SQLAlchemyError as error:
            session.rollback()
            print(error)

        session.close()
        return log_text

    def insert_config_db(self, c_id, msg, session=None):
        """Insert for configs"""
        if session is None:
            session = self.get_session()
        # MESSAGE SORTING CODE: FIND THE CAMERA ID AND MODULE AND UPDATE recent_cam_messages
        log_text = ''
        # row: the index of previous message for this camera and module
        row = self.query_config_db(session, c_id)

        # IF AN ENTRY IS FOUND:
        if row is not None and len(row) != 0:
            log_text = log_text + 'PREVIOUS CONFIG FOUND ({}), REPLACING. '.format(c_id)
            self.delete_db(session, c_id)  # Delete the previous message from the database
        else:
            # THIS IS THE FIRST INSTANCE OF THIS camera_id AND wp_module PAIR
            log_text = log_text + 'THIS IS A NEW CONFIG ({}). '.format(c_id)

        session.add(Configs(conf_id=c_id, msg=msg))
        try:
            session.commit()
        except SQLAlchemyError as error:
            session.rollback()
            print(error)

        session.close()
        return log_text

    def insert_log(self, j_id, timestamp, log):
        """Insert log message"""
        log_session = self.log_db_session()
        log_session.add(Logs(job_id=j_id, time=timestamp, log=log))
        try:
            log_session.commit()
        except SQLAlchemyError as error:
            log_session.rollback()
            print(error)

        log_session.close()

    @staticmethod
    def delete_db(sfn_session, *args):
        try:
            if len(args) == 1:  # """Delete for configs""" # c_id
                sfn_session.query(Configs).filter(Configs.conf_id == args[0]).delete()
            elif len(args) == 2:  # """Delete for recent camera messages"""  # c_id, m_id
                sfn_session.query(Messages).filter(and_(Messages.cam_id == args[0], Messages.module_id == args[1]))\
                    .delete()
        except Exception as error:
            print('error executing deleting from db, error: {}'.format(error))
            return None

    def length_db(self, module_id=None):
        session = self.get_session()
        if module_id is None:
            qr = self.query_db(session)
        else:
            qr = self.query_db(session, None, module_id)
        session.close()
        if qr is None:
            return 0
        else:
            return len(qr)

    def query_db(self, sfn_session, *args):
        """Query the recent camera messages database"""
        session_created = False
        if sfn_session is None:
            sfn_session = self.get_session()
            session_created = True
        rows = []
        try:
            if len(args) == 0:  # No input
                rows = sfn_session.query(Messages).all()
            elif len(args) == 2:
                if args[0] is None:
                    rows = sfn_session.query(Messages).filter(Messages.module_id == args[1]).all()
                elif args[1] is None:
                    rows = sfn_session.query(Messages).filter(Messages.cam_id == args[0]).all()
                else:
                    rows = sfn_session.query(Messages).filter(and_(Messages.cam_id == args[0],
                                                                   Messages.module_id == args[1])).all()

            if session_created:
                sfn_session.close()
            return rows
        except Exception as error:
            print('error executing query, error: {}'.format(error))
            if session_created:
                sfn_session.close()
            return None

    def query_config_db(self, sfn_session, *args):
        """Query the configs database"""
        session_created = False
        if sfn_session is None:
            sfn_session = self.get_session()
            session_created = True
        rows = []
        try:
            if len(args) == 0:  # No input
                rows = sfn_session.query(Configs).all()
            elif len(args) == 1:
                rows = sfn_session.query(Configs).filter(Configs.conf_id == args[0]).all()
            if session_created:
                sfn_session.close()
            return rows
        except Exception as error:
            print('error executing query, error: {}'.format(error))
            if session_created:
                sfn_session.close()
            return None

    def create_reg_message(self, timestamp):
        data = {
                'module_id': self.module_id,
                'type_module': self.module_type,
                'timestamp': str(timestamp),
                'state': self.state,
        }
        message = json.dumps(data)
        # ADD THE REG MESSAGE TO THE DB
        self.insert_config_db(self.module_id, message)
        # message = json.loads(message)
        return message

    @staticmethod
    def send_reg_message(message, url):
        try:
            resp = requests.post(url, data=message, headers={'content-Type': 'application/json'})
        except requests.exceptions.RequestException as e:
            print(e)
            return 'Connection Failed: ' + str(e), 450
        else:
            print('RESPONSE: ' + resp.text + ' ' + str(resp.status_code))
            return 'REG MESSAGE SENT (' + resp.text + str(resp.status_code) + '). ', resp.status_code

    def create_obs_message(self, camera_ids, count, heat_map, timestamp_oldest, timestamp_newest, ground_plane_pos):
        data = {
                'module_id': self.module_id,
                'type_module': self.module_type,
                'camera_ids': camera_ids,
                'density_count': int(count),
                'density_map': heat_map.tolist(),
                'frame_byte_array': '',
                'image_dims': '',
                'ground_plane_position': ground_plane_pos,
                'timestamp_1': timestamp_oldest,
                'timestamp_2': timestamp_newest,
        }
        message = json.dumps(data)
        return message

    @staticmethod
    def load_urls(location, file_name):
        try:
            json_file = open(location + '/' + file_name + '.txt')
        except IOError:
            print('IoError')
        else:
            line = json_file.readline()
            urls = json.loads(line)
            json_file.close()
            print('URLS LOADED: ' + file_name)
            return urls

    @staticmethod
    def generate_amalgamated_top_down_map(top_down_maps, config_for_amalgamation):
        """
        Amalgamate N color images from a list of image paths.
        """
        x = []
        y = []
        w = []
        h = []
        all_rotated_images = []
        for i in range(len(top_down_maps)):
            # Convert from list of lists to matrix
            img = np.array(top_down_maps[i])
            rotated_img = rotate_image(img, config_for_amalgamation[i][2])  # angle

            all_rotated_images.append(rotated_img)
            x.append(config_for_amalgamation[i][0])  # latitude
            y.append(config_for_amalgamation[i][1])  # longitude
            w.append(rotated_img.shape[0])
            h.append(rotated_img.shape[1])

        amalgamation_latitude = min(x)
        amalgamation_longitude = min(y)

        d = [convert_to_meter(f, 0, amalgamation_latitude, 0) for f in x]  # distance
        amalgamation_w = int(max([i + j for i, j in zip(d, w)]))

        d = [convert_to_meter(0, f, 0, amalgamation_longitude) for f in y]  # distance
        amalgamation_h = int(max([i + j for i, j in zip(d, h)]))

        # Generate the amalgamated image
        img_amalgamation = np.zeros(shape=(amalgamation_w, amalgamation_h))

        for i in range(len(all_rotated_images)):
            dis_x = int(convert_to_meter(x[i], 0, amalgamation_latitude, 0))
            dis_y = int(convert_to_meter(0, y[i], 0, amalgamation_longitude))
            img_amalgamation[dis_x:(dis_x + w[i]), dis_y:(dis_y + h[i])] = all_rotated_images[i] + \
                img_amalgamation[dis_x:(dis_x + w[i]), dis_y:(dis_y + h[i])] * (all_rotated_images[i] == 0)

        # cv2.imshow('img_amalgamation', cv2.resize(img_amalgamation, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
        # cv2.waitKey(0)
        # cv2.imwrite('Global_density.png',
        #             cv2.resize(img_amalgamation * 255, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
        amalgamation_ground_plane_position = [amalgamation_latitude, amalgamation_longitude]
        return img_amalgamation, amalgamation_ground_plane_position
