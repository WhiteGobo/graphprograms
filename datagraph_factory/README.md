# algorithm
It takes in the given startvalues and the admired values.
Then it tries to calculate different paths to calulate these values.

it must support loops for imporving algorithms

it uses datagraphs for saving data

it uses states for calculating, which action is taken next.

every calculation step will be saved in contained classes and every of these
classes can fail. Failed classes can be called again.

The state is determined by the data, which is stored inside the datagraph 
and a near-factor to the goal-data. see goal-data-near


## goal data near
The algorithm creates paths in whoch order which calculation can be used.
The order will then be recalculated in a distance of the corresponding 
datagraph states to the goal.

Each of those calculationsteps can fail, and if they do, their branch wont be called again. To ensure that in every branch a calculation can be called indipendent, those calculation will be encapsulated. Each of these capsuls will hold their distance to the goal.

## loops
Ein entscheidendes ding is, dass loops moeglich sind. Deshalb wird die distanz
mittels des datagraphs bestimmt und nicht einfach nur der weg abglaufen. 

Achtung: loops koennen feststecken!!


## distance calculation with datagraphs
For this you need a list of the complete subgraph which is needed at every 
calculation step. The distance will be calculated, with a search algorithm
of these subgraphs in the current datagraph.


You start at the subgraph at the goal. this is your currentsubgraph.

Check if every node and every edge of this current subgraph is conatined in 
the datagraph

If true and the corresponding method hasnt failed this is your current distance

else the next graph in the list will be your current subgraph -- loop

