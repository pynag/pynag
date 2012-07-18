MANPAGES="pynag"
all: manpage

manpage:
	for manpage in $(MANPAGES); do (pod2man --center=$$manpage.pod --release="" $$manpage.pod > $$manpage.1); done

