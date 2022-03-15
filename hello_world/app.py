import json
import jwt
import requests


def get_txid(key):
    jwt_key = requests.get("https://{}".format(key)).text
    print("jwt_key {}".format(jwt_key))

    decoded_key = jwt.decode(jwt_key, options={"verify_signature": False})
    print("decoded_key {}".format(decoded_key))

    txid = decoded_key['txid']
    return txid


def decompose_qr_code(qr_code):
  response_by_id = []

  index = 0
  while index < len(qr_code):
    id = qr_code[index:index+2]
    size = qr_code[index+2:index+4]
    value = qr_code[index+4:index+4+int(size)]
    response_by_id.append({"id":id,"size":size, "value": value})
    index = index+4+int(size)

  return response_by_id


def process_decode_qr_code(qr_code, debug):
  response = {}
  decomposed = decompose_qr_code(qr_code)
  for element in decomposed:
      if int(element['id']) == 54:
        response['amount'] = element['value']
      elif int(element['id']) == 26:
        for proxy_index in decompose_qr_code(element['value']):
          if proxy_index['id'] == '01':
            key = proxy_index['value']
            response['proxy_key'] = key
            response['proxy_type'] = 'static'

          elif proxy_index['id'] == '25':
            key = proxy_index['value']
            response['proxy_key'] = key
            response['proxy_type'] = 'dynamic'
            response['txid'] = get_txid(key)

  if debug:
      response['debug']= decomposed
  return response


def lambda_handler(event, context):
    """PIX QR Code decomposer

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    qr_code = ""
    debug = False
    try:
        print(event)
        request = event['headers']
        qr_code = request['qr_code']
        debug = 'debug' in request

    except requests.RequestException as e:
        # Send some context about this error to Lambda Logs
        print(e)
        raise e

    return {
        "statusCode": 200,
        "body": json.dumps(process_decode_qr_code(qr_code,debug)),
    }
