#!/usr/bin/env python
#python main.py --maxdistance 0.48

from flask import Flask, render_template, Response, session, request, jsonify, json
from werkzeug import secure_filename
from jinja2 import TemplateNotFound
from camera import VideoCamera
import argparse
from datetime import datetime, time
import base64
#from model import Base, session, Participantes, Presenca, Imagesdata
import logging
import threading
import os

app = Flask(__name__)

app.secret_key = 'supersecretkeygoeshere'

app.config['ALLOWED_EXTENSIONS'] = set(['jpg'])

parser = argparse.ArgumentParser()
parser.add_argument("--local", help="", default='', action='store_true')
parser.add_argument("--remote", help="", default='', action='store_true')
#parser.add_argument("--imagespath", help="", default="C:\\Users\\felipe.azevedo\\Desktop\\imagesBD", required=True)
#parser.add_argument("--imagesunknow", help="", default="C:\\Users\\felipe.azevedo\\Desktop\\imagesUnknow", required=True)
parser.add_argument("--maxdistance", help="", default=0.48, required=True)
args = parser.parse_args()

facename = []
name = ""
unrecognizeds = []

threads = list()

vc = VideoCamera(args)


def saveBD(name=None):
    try:
        check_user = session.query(Presenca).filter_by(client_name=name).first()
        if check_user is not None:
            check_user.date_checkin = datetime.now()
        else:
            new_user = Presenca(client_name=name, date_checkin=datetime.now())
            session.add(new_user)
        session.commit()
    except Exception as e:
        raise e


def gen(camera):
    try:
        while True:
            frame, name, unrecognized = camera.get_frame()
            if name is not None:
                if len(name) > 0:
                    # x = threading.Thread(target=saveBD, args=(name,))
                    # threads.append(x)
                    # x.start()
                    facename.append(str(name) + '_' + datetime.now().strftime('%e_%m_%Y_%H_%M_%S') )
            unrecognizeds.append(unrecognized)
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    except Exception as e:
        logging.error(e)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():    
    #return Response(gen(VideoCamera(args)),
    return Response(gen(vc),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/input_photo', methods=['GET','POST'])
def input_photo():
    try:
        if request.method == 'GET':
            return render_template('include_person.html'), 200
        elif request.method == 'POST':
            files = request.files['file-photo']
            person_name = request.form.get("text-name")
            person_phone = request.form.get("text-phone")
            person_email = request.form.get("text-email").split("@")[0]
            person_edomain = request.form.get("text-email").split("@")[1]

            if files and allowed_file(files.filename):
                filename = secure_filename(files.filename)
                
                impath = os.path.join(os.getcwd(), 'updir', filename)
                files.save(impath)

                # Chama a função para incluir nas variaveis do reconhecimento 
                if vc.include_in_database(impath, person_name):
                    # Chama a função para gravar uma nova entrada na tabela participantes                
                    new_user = Participantes(participant_name=person_name, phone=person_phone, email=person_email, domain=person_edomain)
                    session.add(new_user)
                    session.commit()

                    return render_template('include_person.html', alert={'type': 'info', 'msg': 'Foto carregada com sucesso!'}), 200
                else:
                    return render_template('include_person.html', alert={'type': 'danger', 'msg': 'Não foi possível extrair as caracteristicas da Foto, tenta outra foto frontal!'}), 200
        else:
            return jsonify({'error': 'Requisição inválida'}), 200
    except (TemplateNotFound, Exception) as e:
        logging.error(e)


@app.route('/get_content', methods = ['GET'])
def get_content():
    if request.method == 'GET':
        data = {}        
        try:
            listfacenames = facename.copy()
            listunrecognizeds = unrecognizeds.copy()
            data['faces'] = listfacenames
            
            if len(unrecognizeds) > 0:
                if len(listunrecognizeds[0]) > 0:
                    # encoded = base64.encodebytes(listunrecognizeds[0])
                    # encoded = listunrecognizeds[0].encode('base64')
                    #encoded = base64.b64encode(listunrecognizeds[0].tobytes())
                    encoded = base64.encodebytes(listunrecognizeds[0].tobytes()).decode("utf-8")
                    data['unrecognized'] = encoded
                else:
                    encoded = ''
            facename.clear()
            unrecognizeds.clear()
        except Exception as e:            
            logging.error(e)            
        return json.dumps(data)


@app.route('/get_mysql', methods=['GET'])
def get_mysql():
    try:
        if request.method == 'GET':
            participants = session.query(Presenca).all()
            list1 = []
            data = {}
            
            for participant in participants:
                data['participant_name'] = participant.client_name
                data['datetime'] = participant.date_checkin
                list1.append(data.copy())
            
            return jsonify(list1)
    except Exception as e:
        logging.error(e)


if __name__ == '__main__':
    format = "%(asctime)s: [%(pathname)s:%(module)s:%(lineno)d]: %(message)s"    
    logging.basicConfig(filename=os.path.join(os.path.abspath(os.getcwd()), 'app.log'), format=format, level=logging.DEBUG, datefmt="%H:%M:%S")
    logging.info(os.path.join(os.path.abspath(os.getcwd())))
    logging.info("Starting web application")
    app.run(host='0.0.0.0', debug=False)
