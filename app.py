from flask import Flask, request, jsonify, render_template, redirect, session, url_for
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

app = Flask(__name__)
app.secret_key = 'S3cUr3K3Yf0rY0ur4pP!'

def verificar_credenciales(access_key, secret_key):
    try:
        boto3.client('sts', aws_access_key_id=access_key, aws_secret_access_key=secret_key).get_caller_identity()
        return True
    except ClientError:
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        access_key = request.form['access_key']
        secret_key = request.form['secret_key']
        if verificar_credenciales(access_key, secret_key):
            session['access_key'] = access_key
            session['secret_key'] = secret_key
            return redirect(url_for('home'))
        else:
            return jsonify({"error": "Credenciales incorrectas"}), 403
    return render_template('login.html')

@app.route('/home')
def home():
    return "Bienvenido a la Gestión de Documentos Empresariales"

@app.route('/documento', methods=['POST'])
def subir_documento():
    try:
        archivo = request.files['file']
        nombre = archivo.filename
        bucket = 'bucket-empresarial'
        s3 = boto3.client('s3', aws_access_key_id=session['access_key'], aws_secret_access_key=session['secret_key'])
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id=session['access_key'], aws_secret_access_key=session['secret_key'])
        table = dynamodb.Table('Documentos')

        s3.upload_fileobj(archivo, bucket, nombre)

        table.put_item(
            Item={
                'DocumentoID': nombre,
                'Version': '1',
                'Fecha': '2024-06-29'
            }
        )

        return jsonify({"message": "Documento subido con éxito"}), 201

    except KeyError:
        return jsonify({"error": "Archivo no encontrado en la solicitud"}), 400
    except NoCredentialsError:
        return jsonify({"error": "Credenciales no encontradas"}), 400
    except PartialCredentialsError:
        return jsonify({"error": "Credenciales incompletas"}), 400
    except ClientError as e:
        return jsonify({"error": e.response['Error']['Message']}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/documento/<string:documento_id>', methods=['GET'])
def obtener_versiones_documento(documento_id):
    try:
        s3 = boto3.client('s3', aws_access_key_id=session['access_key'], aws_secret_access_key=session['secret_key'])
        response = s3.list_object_versions(Bucket='bucket-empresarial', Prefix=documento_id)
        versiones = response.get('Versions', [])
        return jsonify(versiones), 200

    except NoCredentialsError:
        return jsonify({"error": "Credenciales no encontradas"}), 400
    except PartialCredentialsError:
        return jsonify({"error": "Credenciales incompletas"}), 400
    except ClientError as e:
        return jsonify({"error": e.response['Error']['Message']}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/documento/<string:documento_id>/version/<string:version_id>', methods=['GET'])
def obtener_documento_por_version(documento_id, version_id):
    try:
        s3 = boto3.client('s3', aws_access_key_id=session['access_key'], aws_secret_access_key=session['secret_key'])
        response = s3.get_object(Bucket='bucket-empresarial', Key=documento_id, VersionId=version_id)
        return response['Body'].read(), 200

    except NoCredentialsError:
        return jsonify({"error": "Credenciales no encontradas"}), 400
    except PartialCredentialsError:
        return jsonify({"error": "Credenciales incompletas"}), 400
    except ClientError as e:
        return jsonify({"error": e.response['Error']['Message']}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
