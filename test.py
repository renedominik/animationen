

# Definiere Variable, Namen sind frei gewählt
wert = 3.14
alles = [ "Frank", wert, "Matthias", 21.9 ]


for x in alles:
    # == ist logischer Operator
    if x == "Matthias":
        # wenn richtig
        print( "Hallo", x)
    elif not isinstance(x, str):
        print( "Wert", x)
    # sonst (falsch)
    else:
        print( "Moin", x)


