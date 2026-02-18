from src.Graphs.main_graph import get_main_graph

if __name__ == "__main__":
    app = get_main_graph()
    thread = {"configurable":{"thread_id":"2"}}
    response = app.invoke({"messages":["cancel the booking for booking id 1 for patient id 101 and reason the patient is no longer interested in the appointment"]},config=thread)
    print(response)