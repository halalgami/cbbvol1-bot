import streamlit as st
import random
import time
import boto3
import json
import re


aws_access_key = st.secrets['AWS_ACCESS_KEY']
aws_secret = st.secrets['AWS_SECRET']
aws_bedrock_region = st.secrets['AWS_REGION']
aws_knowledgebase_id = st.secrets['AWS_KB_ID']
aws_bedrock_model_id = 'anthropic.claude-v2'
#aws_bedrock_model_id = 'anthropic.claude-3-haiku'
aws_bedrock_kb_model_arn = 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'

boto_session = boto3.session.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret)

# Streamed response emulator
def response_generator_random():
    response = random.choice(
        [
            "Hello there! How can I assist you today?",
            "Hi, human! Is there anything I can help you with?",
            "Do you need help?",
        ]
    )
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

def bedrock_response_generator(customer_input, current_boto_session):    
    client = current_boto_session.client(
        service_name='bedrock-runtime',
        region_name=aws_bedrock_region
    )
    
    prompt = f"\n\nHuman:{customer_input}\n\nAssistant:"
    
    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": 1000,
        "temperature": 0.75
    })
    response = client.invoke_model(
        body=body,
        modelId=aws_bedrock_model_id,
        accept='application/json',
        contentType='application/json'
    )
    response = json.loads(response.get('body').read())["completion"]

    for word in response.split():
        yield word + " "
        time.sleep(0.05)


def bedrock_kb_response_generator(customer_input, current_boto_session):        
    client = current_boto_session.client(
        service_name='bedrock-agent-runtime',
        region_name=aws_bedrock_region     
    )
    
    api_response = client.retrieve_and_generate(
    input={
        'text': customer_input
    },
    retrieveAndGenerateConfiguration={
    'type':'KNOWLEDGE_BASE',
    'knowledgeBaseConfiguration':{
        'knowledgeBaseId': aws_knowledgebase_id,
        'modelArn': aws_bedrock_kb_model_arn        
        }    
    }
    )
    text_without_refs = api_response["output"]
    #print(teh_response)    
    #response = api_response["output"]['text']

    citations = api_response['citations']

    response = ''
    for i in citations:
        #first we add the text.
        teh_text = i['generatedResponsePart']['textResponsePart']['text']
        teh_ref_temp = i['retrievedReferences'][0]['location']['s3Location']['uri']
        teh_ref = teh_ref_temp.replace("s3://algam-llm-repo/cbbvol1-data/", "").replace(".pdf","")
        response = response + teh_text + " [Referenced Section: "+teh_ref+"] \n\n "
        #st.markdown(response, unsafe_allow_html=True)

    #for word in response.split():
    response = response+"\n\n You go kween! 💅"
    for word in re.split(r'(\s+)', response):
        yield word + " "
        time.sleep(0.05)

st.title("✨ Wafa's CBB Volume 1 Helper ✨")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        #response = st.write_stream(bedrock_response_generator(prompt,boto_session))
        response = st.write_stream(bedrock_kb_response_generator(prompt,boto_session))
    

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    

    