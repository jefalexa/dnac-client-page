import json
from flask import (Flask, redirect, render_template, request, url_for)
import dnac

app = Flask(__name__)

# Testing Paramaters
use_static_data = False
use_static_client_id = True


@app.route('/')
def form01():
    return render_template('portal/form.html')
 

@app.route('/client', methods = ['POST', 'GET'])
def portal():
    if request.method == 'GET':
        return redirect("/")
    if request.method == 'POST':
        form_data = request.form
        userid = form_data['userid']
        if use_static_data:
            with open('client_data_static_display.json', 'r') as file: 
                client_details_list_display = json.load(file)
        else:
            if use_static_client_id:
                entity_type = 'mac_address'
                entity_value = '1C:6A:7A:E0:6F:27'
                client_details_list_display = dnac.get_client_details_display(entity_type, entity_value)
            else:
                entity_type = 'network_user_id'
                entity_value = userid
                client_details_list_display = dnac.get_client_details_display(entity_type, entity_value)
        return render_template('portal/index.html', data=client_details_list_display, userid=userid)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8008, debug=False) 

