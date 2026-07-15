import chainlit as cl
from services.llm import generate_response

@cl.on_chat_start
def on_chat_start():
    print("Bonjour")

@cl.on_message
async def main(message: cl.Message):
    # Your custom logic goes here...
    # llm_answer = generate_response(message.content)
    # # Send a response back to the user
    # await cl.Message(
    #     content=f"Received: {llm_answer}",
    # ).send()
    try:
        response = generate_response(message.content)
        if not response:
            response = "Réponse vide (fallback)"
        await cl.Message(content=str(response)).send()
    except Exception as e:
        await cl.Message(content=f"Erreur: {e}").send()
    
@cl.set_starters # type: ignore
async def set_starters():
    return [
        cl.Starter(
            label="Quels types de produits sont collectés auprès des entreprises ?",
            message="Quels types de produits sont collectés auprès des entreprises ?",
        ),
        cl.Starter(
            label="Qu'est-ce que la Quincaillerie Solidaire ?",
            message="Qu'est-ce que la Quincaillerie Solidaire ?",
        ),
        cl.Starter(
            label="Quelle sont les valeurs de votre association",
            message="Quelle sont les valeurs de votre association",
        ),
    ]