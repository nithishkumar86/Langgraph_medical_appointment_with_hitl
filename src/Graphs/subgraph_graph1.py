from langgraph.graph import StateGraph,START,END
from src.Graph_States.graph_design import State
from src.Sub_Agent1.subagent_workflow1 import Booking_Node, email_body_generator, send_email, router_for_email_body_generator
from langsmith import traceable

@traceable(name="subgraph1", metadata={"subgraph1": "subgraph1_execution"})
def create_subgraph():
    subgraph_builder = StateGraph(State)

    subgraph_builder.add_node('booking_node', Booking_Node)
    subgraph_builder.add_node('email_body_generator_node', email_body_generator)
    subgraph_builder.add_node('send_email_node', send_email)
    subgraph_builder.add_conditional_edges("booking_node",router_for_email_body_generator)
    subgraph_builder.add_edge(START, 'booking_node')
    subgraph_builder.add_edge('booking_node', 'email_body_generator_node')
    subgraph_builder.add_edge('email_body_generator_node', 'send_email_node')
    subgraph_builder.add_edge('send_email_node', END)

    subgraph = subgraph_builder.compile()
    return subgraph