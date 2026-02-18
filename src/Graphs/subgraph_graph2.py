from langgraph.graph import StateGraph,START,END
from src.Graph_States.graph_design import State
from src.Sub_Agent2.subgraph_workflow2 import validate_cancellation,router_for_hitl_path,cancellation_hitl,router_for_booking_cancellation_email,cancel_booking,router_for_booking_cancellation_email,cancel_email_body,send_cancellation_email,router_for_hitl_cancellation
from langsmith import traceable


@traceable(name="subgraph2", metadata={"subgraph1": "subgraph2_execution"})
def create_cancellation_subgraph():
    subgraph_builder1 = StateGraph(State)

    subgraph_builder1.add_node("validate_cancellation_node",validate_cancellation)
    subgraph_builder1.add_node("cancellation_hitl_node",cancellation_hitl)
    subgraph_builder1.add_node("cancel_booking_node",cancel_booking)
    subgraph_builder1.add_node("cancel_email_body_node",cancel_email_body)
    subgraph_builder1.add_node("send_cancellation_email_node",send_cancellation_email)
    subgraph_builder1.add_edge(START,"validate_cancellation_node")

    subgraph_builder1.add_conditional_edges("validate_cancellation_node",router_for_hitl_path)

    subgraph_builder1.add_conditional_edges("cancellation_hitl_node",router_for_hitl_cancellation)
    subgraph_builder1.add_conditional_edges("cancel_booking_node",router_for_booking_cancellation_email)
    subgraph_builder1.add_edge("cancel_email_body_node","send_cancellation_email_node")
    subgraph_builder1.add_edge("send_cancellation_email_node",END)

    subgraph1 = subgraph_builder1.compile()

    return subgraph1
