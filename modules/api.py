import json

import gradio as gr

from modules import shared
from modules.text_generation import generate_reply
from modules.chat import chatbot_wrapper, save_history

chat_api = {
    'enabled': False,
}

# set this to True to rediscover the fn_index using the browser DevTools
VISIBLE = False

def generate_reply_wrapper(string):
    global chat_api

    # Provide defaults so as to not break the API on the client side when new parameters are added
    generate_params = {
        'max_new_tokens': 200,
        'do_sample': True,
        'temperature': 0.5,
        'top_p': 1,
        'typical_p': 1,
        'repetition_penalty': 1.1,
        'encoder_repetition_penalty': 1,
        'top_k': 0,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'seed': -1,
        'add_bos_token': True,
        'custom_stopping_strings': [],
        'truncation_length': 2048,
        'ban_eos_token': False,
        'skip_special_tokens': True,
    }
    params = json.loads(string)

    if chat_api['enabled']:
        # Overwrite values from UI with values sent to API method
        for k in params[1]:
            chat_api.update({k: params[1][k]})

        # Back up the old no_stream value and set no_stream to True (required for API to work correctly)
        no_stream = shared.args.no_stream
        shared.args.no_stream = True

        for i in chatbot_wrapper(params[0], chat_api, True, False):
            # I'm not sure how to do this properly in Python, this is just basically letting the generator finish. I did the yield shared.history['visible'][-1] here, but then I couldn't force the save or reset the streaming variable
            pass
        
        # Reset no_stream to backed up value
        shared.args.no_stream = no_stream

        # Save prompt and reply to persistent chat log
        save_history(chat_api['mode'], timestamp=False)

        yield shared.history['visible'][-1]
    else:
        generate_params.update(params[1])
        for i in generate_reply(params[0], generate_params):
            yield i

def create_apis():
    global chat_api

    t1 = gr.Textbox(visible=VISIBLE)
    t2 = gr.Textbox(visible=VISIBLE)
    dummy = gr.Button(visible=VISIBLE)


    input_params = [t1]
    output_params = [t2] + [shared.gradio[k] for k in ['display']] if chat_api['enabled'] else [shared.gradio[k] for k in ['markdown', 'html']]
    dummy.click(generate_reply_wrapper, input_params, output_params, api_name='textgen')

def create_chat_apis():
    global chat_api
    
    # Set up the chat_api dict
    for k in shared.input_elements:
        chat_api.update({k: shared.gradio[k].value})

    chat_api['enabled'] = True

    # Set up change event listeners for the fields we care about for chat
    shared.gradio['name1'].change(lambda x: chat_api.update({'name1': x}), shared.gradio['name1'], [])
    shared.gradio['name2'].change(lambda x: chat_api.update({'name2': x}), shared.gradio['name2'], [])
    shared.gradio['context'].change(lambda x: chat_api.update({'context': x}), shared.gradio['context'], [])
    shared.gradio['custom_stopping_strings'].change(lambda x: chat_api.update({'custom_stopping_strings': x}), shared.gradio['custom_stopping_strings'], [])
    shared.gradio['mode'].change(lambda x: chat_api.update({'mode': x}), shared.gradio['mode'], [])
    shared.gradio['end_of_turn'].change(lambda x: chat_api.update({'end_of_turn': x}), shared.gradio['end_of_turn'], [])

    # Then call the default create_apis function
    create_apis()
