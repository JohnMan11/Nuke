# Nuke

NodeLister:

This tool can be launched by copying the code and pasting in the Script Editor in NUKE.

This nuke tool lists all nodes found in the current nuke script.  It organizes them by node class.
There is a name search field which hides all nodes that do not match the node name search.  It is not case-sensative.
There is a button to toggle the expansion and collapse of the rows of the node classes.

In the tree itself, there are only two columns: Name and Disable.
There are two types of rows: ClassRows and NodeRows (sub rows)
Clicking on the Name column in the NodeRow will center zoom the node in the DAG.
Clicking on the Disable column in the NodeRow will disable the node in the script.
Clicking on the Disable column in the ClassRow will disable all nodes of that class.


SequenceCompare:

This tool was created to test sequences to see if they were redeliveries from the client.

It checks frame by frame until it finds a frame with a difference.

I'll probably embed this into a group or gizmo.
