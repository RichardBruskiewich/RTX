import sys
import os
import importlib
from tomark import Tomark
import re
import md_toc
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../ARAXQuery")
modules = ["ARAX_messenger", "ARAX_expander", "ARAX_overlay", "ARAX_filter_kg", "ARAX_filter_results", "ARAX_resultify"]
classes = ["ARAXMessenger", "ARAXExpander", "ARAXOverlay", "ARAXFilterKG", "ARAXFilterResults", "ARAXResultify"]
modules_to_command_name = {'ARAX_resultify': '`resultify()`', 'ARAX_messenger': '`create_message()`',
                           'ARAX_overlay': '`overlay()`', 'ARAX_filter_kg': '`filter_kg()`','ARAX_filter_results': '`filter_results()`', 
                           'ARAX_expander': '`expand()`'}
to_print = ""
header_info = """
# Domain Specific Langauage (DSL) description
This document describes the features and components of the DSL developed for the ARA Expander team.

Full documentation is given below, but an example can help: in the API specification, there is field called `Query.previous_message_processing_plan.processing_actions:`,
while initially an empty list, a set of processing actions can be applied with something along the lines of:

```
[
"add_qnode(name=hypertension, id=n00)",  # add a new node to the query graph
"add_qnode(type=protein, is_set=True, id=n01)",  # add a new set of nodes of a certain type to the query graph
"add_qedge(source_id=n01, target_id=n00, id=e00)",  # add an edge connecting these two nodes
"expand(edge_id=e00)",  # reach out to knowledge providers to find all subgraphs that satisfy these new query nodes/edges
"overlay(action=compute_ngd)",  # overlay each edge with the normalized Google distance (a metric based on Edge.source_id and Edge.target_id co-occurrence frequency in all PubMed abstracts)
"filter_kg(action=remove_edges_by_attribute, edge_attribute=ngd, direction=above, threshold=0.85, remove_connected_nodes=t, qnode_id=n01)",  # remove all edges with normalized google distance above 0.85 as well as the connected protein
"return(message=true, store=false)"  # return the message to the ARS
]
```
 
# Full documentation of current DSL commands
"""
to_print += header_info
#for (module, cls) in zip(modules, classes):
#    m = importlib.import_module(module)
#    #print(getattr(m, cls)().describe_me())
#    dsl_name = modules_to_command_name[module]
#    to_print += f"# {module}\n"
#    to_print += f"|{dsl_name} DSL commands\n"
#    for dic in getattr(m, cls)().describe_me():
#        #to_print += Tomark.table([dic])
#        #to_print += "\n"
#        temp_table = Tomark.table([dic])
#        temp_table_split = temp_table.split("\n")
#        better_table = f"|{dsl_name} DSL commands" + ('|' * temp_table_split[0].count('|')) + '\n'
#        better_table += temp_table_split[1] + '-----|\n'
#        better_table += '|**DSL parameters**' + temp_table_split[0] + "\n"
#        better_table += '|**DSL arguments**' + temp_table_split[2] + "\n"
#        to_print += better_table + '\n'

for (module, cls) in zip(modules, classes):
    m = importlib.import_module(module)
    dsl_name = modules_to_command_name[module]
    to_print += f"## {module}\n"
    for dic in getattr(m, cls)().describe_me():
        if 'action' in dic:  # for classes that use the `action=` paradigm
            action = dic['action'].pop()
            del dic['action']
            to_print += '### ' + re.sub('\(\)',f'(action={action})', dsl_name) + '\n'
        elif 'dsl_command' in dic:  # for classes like ARAX_messenger that have different DSL commands with different top level names as methods to the main class
            dsl_command = dic['dsl_command']
            del dic['dsl_command']
            #to_print += '### ' + re.sub('\(\)', f'({subcommand}=)', dsl_name) + '\n'
            to_print += '### ' + dsl_command + '\n'
        else:  # for classes that don't use the `action=` paradigm like `expand()` and `resultify()`
            to_print += '### ' + dsl_name + '\n'
        if 'brief_description' in dic:
            to_print += dic['brief_description'] + '\n\n'
            del dic['brief_description']
        if dic:  # if the dic is empty, then don't create a table
            temp_table = Tomark.table([dic])
            temp_table_split = temp_table.split("\n")
            #better_table = "|"+re.sub('\(\)',f'(action={action})', dsl_name) + ('|' * temp_table_split[0].count('|')) + '\n'
            better_table = ('|' * (temp_table_split[0].count('|')+1)) + '\n'
            better_table += temp_table_split[1] + '-----|\n'
            better_table += '|_DSL parameters_' + temp_table_split[0] + "\n"
            better_table += '|_DSL arguments_' + temp_table_split[2] + "\n"
            to_print += better_table + '\n'
        else:
            to_print += '\n'

file_name = 'DSL_Documentation.md'
fid = open(file_name, 'w')
fid.write(to_print)
fid.close()

with_toc = "# Table of contents\n\n"
with_toc += md_toc.build_toc(os.path.dirname(os.path.abspath(__file__)) + '/' + file_name)
with_toc += to_print
fid = open(file_name, 'w')
fid.write(with_toc)
fid.close()

