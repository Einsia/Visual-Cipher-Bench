"""Drawing layout coordinates only, shared with PNG reader."""
WIDTH,HEIGHT=2400,1700
TILES={1:[
 ((150,365,455,980),(40,265)),
 ((635,295,1565,945),(420,265)),
 ((130,980,1570,1465),(650,995)),
 ((130,1470,950,1830),(1490,300)),
 ((130,1830,650,1890),(1490,660)),
 ((130,1895,640,2070),(45,1415)),
 ((690,1850,1530,2180),(1490,760)),
],2:[]}
for k,x in enumerate([362,850,1338]):
 row=250+470*k
 for (lo,hi),dest in zip([(385,774),(1067,1448)],[(250,row),(850,row)]):
  TILES[2].append(((x-225,lo,x+225,hi),dest))
CATALOG=[(280+460*(i%3),400+360*(i//3)) for i in range(9)]
CAT_UNIT=20
CAT_NUMBER_OFFSET=(-215,-120)
CAT_SAME_GRID_Y=1330
OBS_ORIGIN=(1850,650)
OBS_UNIT=22
OBS_BOUNDS=(-12,17,-10,12)
EXIT_X=[280+220*j for j in range(9)]
EXIT_Y=1450
PAIR_X=[1810,1910]
PAIR_Y=320

# One-round independent opaque rehearsal, on landscape page 2.
CHECK_LAYER_X=[2000,2100,2200,2300]
CHECK_LAYER_Y=310
CHECK_ANGLES_Y=380
CHECK_ORIGINS=[(2010,550),(2240,550)]
CHECK_UNIT=18
CHECK_LABEL_Y=425
