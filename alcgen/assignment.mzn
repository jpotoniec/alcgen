int: n;
array[_] of tuple(int, int): different;
%array[_] of array[_] of tuple(int, int): pairs;

set of int: VARS = 1..n;
array[VARS] of var int: ass;
var set of VARS: used;

constraint forall(v in VARS)(abs(ass[v]) >= 1 /\ abs(ass[v]) <= n);
constraint forall(i in different)(abs(ass[i.1]) != abs(ass[i.2]));
constraint forall(i in index_set(pairs))(exists(j in index_set(pairs[i]))(ass[pairs[i][j].1] == -ass[pairs[i][j].2]));
%constraint forall(u in used)(exists(v in VARS)(abs(ass[v]) == u));
constraint forall(u in used)(ass[u] == u);
solve maximize card(used);
