#praat script: ph_ofrom.praat
# 15.03.2024
# 
# Calls "Align interval" on each valid interval of each tier of a TextGrid.
# Use another script to loop over files/folders.
#
# form:
# - aud_path (sentence): path to audio file 
# - tgd_path (sentence): path to TextGrid file
# - ph_path (sentence):  path for the TextGrid file to output (can overwrite)
# - regT (word):         regex to parse valid tiers (not in label)
# - regI (word):         regex to parse valid intervals (not in label)
# - ch_close (boolean):  whether to close the GUI at script end (console call)
# 
# procedures:
# - 'iterate': reads each tier of a file (calls 'treat_tier')
#              that tier is extracted 'tmpTGD' then merged (call 'merge_tmp')
# - 'merge_tmp': merges the final textgrid 'phTGD' and 'tmpTGD'
# - 'treat_tier': stores start/end/label of each interval in vectors
#                 then opens editor and calls 'treat_part' on each interval
# - 'treat_part': runs 'Align interval' if the label is valid and duration 
#                 >= 0.032s.
# 
# Error messages:
# - Sound shorter than window length: 			most likely invalid label
# - Cannot change the domain: 					cause not found.
# - Domains not equal: 							cause not found. 
# - Domains Sound & Textgrid should be equal: 	cause not found.
# - Slope constraint: 							cause not found. Still processes?
#   											remains even with 'nocheck'
#
# Note: The script has no form for 'Alignment settings' (see 'treat_tier').
# Note: The script has a 'nowarn nocheck' on 'Align interval'
# Note: Invalid intervals will generate no corresponding interval in new tiers
#       (words/phones). Use another script to fill the gaps.
## 

form: "phonemic alignment"
	sentence: "aud_path",""
	sentence: "tgd_path",""
	sentence: "ph_path",""
	word: "regT","[\[/]"
	word: "regI","[_#@%]"
	boolean: "ch_close",0
endform

procedure treat_part
	if index_regex(tlabel$#[ni],regI$) == 0 & (tend#[ni]-tstart#[ni]) >= 0.032
		Select: tstart#[ni],tend#[ni]
		nowarn nocheck Align interval
	endif
endproc

procedure treat_tier
	selectObject: tmpTGD
	nIntervals = Get number of intervals... 1
	tstart# = zero# (nIntervals)
	tend# = zero# (nIntervals)
	tlabel$# = empty$# (nIntervals)
	for ni from 1 to nIntervals
		tstart#[ni] = Get start point: 1,ni
		tend#[ni] = Get end point: 1, ni
		tlabel$#[ni] = Get label of interval: 1, ni
	endfor
	selectObject: mySound,tmpTGD
	View & Edit
	editor: tmpTGD
		Alignment settings: "French (Switzerland)","yes","yes","no"
		for ni from 1 to nIntervals
			call treat_part
		endfor
		Close
	endeditor
	selectObject: myTGD
endproc

procedure merge_tmp
	if it == 1
		phTGD = tmpTGD
	else
		selectObject: phTGD,tmpTGD
		newTGD = Merge
		selectObject: phTGD,tmpTGD
		Remove
		phTGD = newTGD
	endif
	selectObject: myTGD
endproc

procedure iterate
	mySound = Open long sound file... 'aud_path$'
	myTGD = Read from file... 'tgd_path$'
	selectObject: myTGD
	nTiers = Get number of tiers
	for it from 1 to nTiers
		tname$ = Get tier name: it
		tmpTGD = Extract one tier... it
		selectObject: tmpTGD
		if index_regex(tname$,regT$) == 0
			call treat_tier
		endif
		call merge_tmp
	endfor
	selectObject: phTGD
	Write to text file... 'ph_path$'
	selectObject: mySound,myTGD,phTGD
	Remove
	if ch_close
		Quit
	endif
endproc

call iterate