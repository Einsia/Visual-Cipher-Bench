"""Generic English word and two-word phrase knowledge used to confirm and order extracted words.

W5/W_OTHER are a broad list of common words. PHRASES is a general list of common English open compounds
(phrases a solver would recognise); it is used only to decide the order of two extracted words.
"""
W = set("""about above actor adapt admit adopt adult after again agent agree ahead alarm album alert alike alive allow alone
along alter angel anger angle angry apart apple apply arena argue arise array arrow aside asset audio avoid award aware
bacon badge baker basic basin batch beach beard beast begin being below bench berry birth black blade blame blank blast
blaze blend blind block blood bloom board boast bonus boost booth bound brain brake brand brass brave bread break breed
brick bride brief bring broad brook brown brush build bunch burst buyer cabin cable camel canal candy canoe cargo carry
carve catch cause chain chair chalk chant chaos charm chart chase cheap cheat check cheek cheer chess chest chief child
chill choir chord civic civil claim clash class clean clear clerk click cliff climb clock close cloth cloud coach coast
coral couch count court cover crack craft crane crash crawl cream creek crime crisp cross crowd crown crude cruel crush
curve cycle daily dairy dance death debut decay delay depth diary dirty ditch dozen draft drain drama dream dress drift
drill drink drive dwell eager eagle early earth eight elbow elder elect empty enemy enjoy enter entry equal error essay
event every exact exist extra fable faint faith false fancy feast fence ferry fetch fever field fifth fifty fight final
flame flash fleet flesh float flock flood floor flour fluid flute focus force forge forth forty forum found frame frank
fresh front frost fruit giant given glass globe glory glove grace grade grain grand grant grape graph grasp grass grave
great green greet grief grill grind gross group guard guess guest guide habit happy harsh haste heart heavy hedge hello
honey honor horse hotel house human humor hurry ideal image index inner input issue ivory jewel joint judge juice knife
knock label labor large laser later laugh layer learn lease least leave legal lemon level light limit linen liver lobby
local lodge logic loose lover lower loyal lucky lunch magic major maker manor maple march match mayor medal media mercy
merit metal meter minor model money month moral motor mount mouse mouth movie music nerve never night noble noise north
novel nurse ocean offer often olive onion opera orbit order organ other ounce outer owner paint panel panic paper party
paste patch pause peace peach pearl penny phase phone photo piano piece pilot pinch pitch pizza place plain plane plant
plate plaza point polar porch pound power press price pride prime print prior prize proof proud prove pupil purse queen
quick quiet quite quote radar radio raise rally range rapid ratio reach react ready realm rebel refer relax reply rider
ridge rifle right rigid river roast robin rocky rough round route royal rural saint salad sauce scale scarf scene scope
score scout scrap screw sense serve seven shade shake shape share shark sharp sheep sheet shelf shell shift shine shirt
shock shoot shore short shout sight silly skill skirt slate sleep slice slide slope small smart smile smoke snake solar
solid solve sound south space spade spare spark speak speed spell spend spice spine spoon sport spray squad stack staff
stage stain stake stall stamp stand stare start state steam steel steep stern stick still stock stone stool store storm
story stove strap straw strip study style sugar suite sunny super swamp swear sweat sweet swift swing sword table taste
teach tease tempo thank theme thick thief thing think third thorn three throw thumb tiger tight timer title toast today
token tooth topic torch total touch tough tower toxic trace track trade trail train trait trash treat trend trial tribe
trick troop truck truly trunk trust truth tulip twice twist uncle under union unity upper upset urban usage usual valid
value vapor vault venue verse video vigor virus visit vital vivid vocal voice voter wagon waste watch water weave wedge
weird whale wheat wheel which while white whole width witch woman world worry worth wound wrist write wrong yacht yield
young youth zebra acorn amber ankle aroma beret caper ember heron lapel lemur pacer perch poker prone spear spree taper recap
pears reaps spare parse""".split())

PHRASES = {tuple(p.split()) for p in """
paper chase|paper trail|paper plane|paper clip|paper route|paper money|paper towel|paper tiger|paper weight|paper mill
car chase|wild goose chase|steeple chase|chase scene|chain store|chain mail|chain gang|chair lift|stone wall|stone age
water level|water table|water tower|green light|green house|brass band|chalk board|black board|black market|black sheep
board game|board room|power plant|power point|power play|light house|light year|house party|party line|front line
front door|front page|stage fright|stage coach|grand piano|grand prize|grand stand|stock market|stock price|price tag
price point|trade mark|trade wind|trade route|track record|track meet|train track|train station|truck stop|world class
world record|first class|class act|field trip|field day|game plan|flash light|flash point|fire place|fire drill|fire alarm
alarm clock|clock tower|tower block|block party|night shift|night watch|watch tower|sweet heart|heart beat|space ship
ship shape|shape shift|time line|line dance|dance floor|floor plan|plan ahead|test drive|drive train|train wreck
bread board|bread crumb|crumb trail|trail head|trail mix|head start|start line|finish line|check point|check mark
""".replace("\n", "|").split("|") if p.strip()}


def is_word(s):
    return s.lower() in W


def is_phrase(a, b):
    return (a.lower(), b.lower()) in PHRASES
