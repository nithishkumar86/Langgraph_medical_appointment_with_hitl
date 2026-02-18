from langgraph.graph import StateGraph,START,END
from src.Graph_States.graph_design import State
from src.Agent.agent import classify_to_router,question_extractor_for_booking,question_extractor_for_cancelling,check_slots_remaining,aggragator_function,Human_in_the_loop,hitl_router,Update_Complete_Booking_Detail,Condition_Check,Fetch_doctor_availability
from src.Graphs.subgraph_graph1 import create_subgraph
from src.Graphs.subgraph_graph2 import create_cancellation_subgraph
from langgraph.checkpoint.memory import MemorySaver
from langsmith import traceable

subgraph = create_subgraph()
subgraph1 = create_cancellation_subgraph()

@traceable(name="main_graph",metadata={"main_graph": "main graph execution"})
def get_main_graph():
    graph = StateGraph(State)

    graph.add_node("Router_node",classify_to_router)
    graph.add_node("question_extractor_for_booking_node",question_extractor_for_booking)
    graph.add_node("question_extractor_for_cancelling_node",question_extractor_for_cancelling)
    graph.add_node("Fetch_doctor_availability_node",Fetch_doctor_availability)
    graph.add_node("check_slots_remaining_node",check_slots_remaining)
    graph.add_node("aggragator_function_node",aggragator_function)
    graph.add_node("cancellation_node",subgraph1)
    graph.add_node("human_in_the_loop_node1",Human_in_the_loop)
    graph.add_node("update_complete_booking_detail_node",Update_Complete_Booking_Detail)
    graph.add_node("booking",subgraph)
    graph.add_edge(START,"Router_node")


    graph.add_conditional_edges("Router_node",Condition_Check)

    #booking
    graph.add_edge("question_extractor_for_booking_node","Fetch_doctor_availability_node")
    graph.add_edge("Fetch_doctor_availability_node","check_slots_remaining_node")
    graph.add_edge("check_slots_remaining_node","aggragator_function_node")
    graph.add_edge("aggragator_function_node","human_in_the_loop_node1")
    graph.add_edge("update_complete_booking_detail_node","booking")
    graph.add_edge("booking",END)
    graph.add_edge("cancellation_node",END)

    graph.add_conditional_edges("human_in_the_loop_node1",hitl_router)


    # cancellation
    graph.add_edge("question_extractor_for_cancelling_node","cancellation_node")
    graph.add_edge("cancellation_node",END)

    memory = MemorySaver()

    app = graph.compile(checkpointer=memory)

    return app

