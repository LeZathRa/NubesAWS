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

def obtener_rol_usuario(access_key, secret_key):
    iam = boto3.client('iam', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    user_arn = iam.get_user()['User']['Arn']
    user_name = user_arn.split('/')[-1]
    attached_policies = iam.list_attached_user_policies(UserName=user_name)
    roles = []
    for policy in attached_policies['AttachedPolicies']:
        if policy['PolicyName'] == 'AdminPolicies':  # Ajustar según el nombre exacto de tu política
            roles.append('admin')
        else:
            roles.append('user')
    return roles

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        access_key = request.form['access_key']
        secret_key = request.form['secret_key']
        if verificar_credenciales(access_key, secret_key):
            session['access_key'] = access_key
            session['secret_key'] = secret_key
            session['user_roles'] = obtener_rol_usuario(access_key, secret_key)
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Credenciales incorrectas")
    return render_template('login.html')

@app.route('/home')
def home():
    if 'user_roles' in session:
        return render_template('home.html', user_roles=session['user_roles'], title="Home")
    return redirect(url_for('login'))

@app.route('/subir_documento', methods=['GET'])
def mostrar_formulario_subir_documento():
    return render_template('subir_documento.html', title="Subir Documento")

@app.route('/documento', methods=['POST'])
def subir_documento():
    if 'access_key' not in session or 'secret_key' not in session:
        return redirect(url_for('login'))
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

@app.route('/documentos')
def listar_documentos():
    if 'access_key' not in session or 'secret_key' not in session:
        return redirect(url_for('login'))
    try:
        s3 = boto3.client('s3', aws_access_key_id=session['access_key'], aws_secret_access_key=session['secret_key'])
        response = s3.list_objects_v2(Bucket='bucket-empresarial')
        archivos = response.get('Contents', [])
        return render_template('listar_documentos.html', archivos=archivos, title="Lista de Documentos")

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
    if 'access_key' not in session or 'secret_key' not in session:
        return redirect(url_for('login'))
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
    if 'access_key' not in session or 'secret_key' not in session:
        return redirect(url_for('login'))
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

@app.route('/almacenamiento')
def almacenamiento():
    if 'access_key' not in session or 'secret_key' not in session:
        return redirect(url_for('login'))
    try:
        s3 = boto3.client('s3', aws_access_key_id=session['access_key'], aws_secret_access_key=session['secret_key'])
        response = s3.list_objects_v2(Bucket='bucket-empresarial')
        archivos = response.get('Contents', [])
        return render_template('almacenamiento.html', archivos=archivos, title="Almacenamiento")

    except NoCredentialsError:
        return jsonify({"error": "Credenciales no encontradas"}), 400
    except PartialCredentialsError:
        return jsonify({"error": "Credenciales incompletas"}), 400
    except ClientError as e:
        return jsonify({"error": e.response['Error']['Message']}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/destacados')
def destacados():
    if 'access_key' not in session or 'secret_key' not in session:
        return redirect(url_for('login'))
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id=session['access_key'], aws_secret_access_key=session['secret_key'])
        table = dynamodb.Table('DocumentosDestacados')
        response = table.scan()
        documentos = response.get('Items', [])
        return render_template('destacados.html', documentos=documentos, title="Documentos Destacados")

    except NoCredentialsError:
        return jsonify({"error": "Credenciales no encontradas"}), 400
    except PartialCredentialsError:
        return jsonify({"error": "Credenciales incompletas"}), 400
    except ClientError as e:
        return jsonify({"error": e.response['Error']['Message']}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/destacar_documento', methods=['POST'])
def destacar_documento():
    if 'access_key' not in session or 'secret_key' not in session:
        return redirect(url_for('login'))
    try:
        documento_id = request.form['documento_id']
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id=session['access_key'], aws_secret_access_key=session['secret_key'])
        table = dynamodb.Table('DocumentosDestacados')
        
        table.put_item(
            Item={
                'DocumentoID': documento_id
            }
        )
        return jsonify({"message": "Documento destacado con éxito"}), 201

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
