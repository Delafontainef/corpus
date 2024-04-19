import sys,os,re,subprocess,shutil
from corflow import fromPraat,toPraat
PH_HOME = os.path.abspath(os.path.dirname(__file__))

    # for post_clean() > _ac()
r_one = r"[aàâáeéêèiíîìoóôòuúûùy]"
r_two = r"[bcdfghjklmnpqrstv]"
r_three = r"[xz]"
d_else = {'w':6}
    # for clean()
re_syms = "[#@%]"

    # post-cleaning
def _split_left(ph_tier,wd_tier,seg,sym):
    """Splits apostrophes ["c'","d'","j'","l'","m'","n'","qu'","s'","t'"]."""
    ph_seg = ph_tier.getTime(seg.start)
    if (not ph_seg) or (ph_seg.content == sym):
        mid = int(seg.start+((seg.end-seg.start)/2))
    else:
        mid = ph_seg.end
    c1,c2 = seg.content.split("'",1)
    nseg = wd_tier.create(seg.index(),"",seg.start,mid,c1+"'")
    seg.start = mid; seg.content = c2
    return nseg
def _split_right(ph_tier,wd_tier,seg,sym):
    """Splits ending 'à' for some reason."""
    c1,c2 = seg.content.rsplit(" ",1)
    i,c = 1,c2.lower()          # assume 'c' is a vowel
    if c == "w":                # don't handle 'w' just yet...
        return seg
    if re.match(r_two,c):       # if consonant
        i = 2
    elif re.match(r_three,c):   # 3-length consonants
        i = 3
    ph_seg = ph_tier.getTime(seg.end-0.001) # phone
    if (not ph_seg) or (ph_seg.content == sym): # "?" case or no phone
        mid = int(seg.start+((seg.end-seg.start)/2))
    else:
        for ai in range(i-1):   # get starting phone
            ph_seg = ph_tier.elem[ph_seg.index()-1]
        mid = ph_seg.start
    nseg = wd_tier.create(seg.index(),"",mid,seg.end,c2)
    seg.end = mid; seg.content = c1
    return nseg
def post_clean(f,nf="",sym="?"):
    """Cleans dates, apostrophes, etc."""
    nf = f if not nf else nf                                # output path
    trans = fromPraat.fromPraat(f)
    for ph_tier in trans:
        if not "[phon]" in ph_tier.name:                    # phon tier
            continue
        tn = ph_tier.name.split("[",1)[0]
        wd_tier = trans.getName(tn+"[word]")                # word tier
            # for each segment
        for a in range(len(wd_tier)-2,-1,-1):               # segments
            seg1,seg2 = wd_tier.elem[a],wd_tier.elem[a+1]
            if re.search(r" .$",seg2.content):
                _split_right(ph_tier,wd_tier,seg2,sym)
            if re.match(r"^(c'|d'|j'|l'|m'|n'|qu'|s'|t').+",seg2.content):
                _split_left(ph_tier,wd_tier,seg2,sym); continue
            if (re.search(r"\d$",seg1.content) and 
                 re.match(r"^\d",seg2.content)):            # numbers
                seg1.end = seg2.end
                seg1.content = seg1.content+seg2.content
                wd_tier.pop(a+1); continue
            elif (re.match(r"^\w$",seg1.content) and 
                  " " in seg2.content):                     # weird splits
                c1,c2 = seg2.content.split(" ",1)
                seg1.content = seg1.content+c1
                seg2.content = c2
            # last segment (wd_tier.elem[0])
        if re.match(r"^(c'|d'|j'|l'|m'|n'|qu'|s'|t').+",seg1.content):
            _split_left(ph_tier,wd_tier,seg1,sym)
        if re.search(r" .{1}$",seg1.content):
            _split_right(ph_tier,wd_tier,seg1,sym)
    trans.renameSegs()                                      # segments IDs
    toPraat.toPraat(nf,trans)                               # save TextGrid
    # sub-functions
def post_align(f,nf="",sym_i="",sym_p="_",sym="?"):
    """Rename anno-tiers and adds 'filler' segments."""
    nf = f if not nf else nf                                # output path
    trans = fromPraat.fromPraat(f)
    for tier in trans:
        if not "/" in tier.name:                            # alignment tiers
            continue
        tier.name = tier.name.replace("/","[")+"]"          # rename
        ptier = trans.findName(tier.name.split("[",1)[0])
        if not ptier:                                       # should not happen
            continue
        for a in range(len(tier)-1,-1,-1):                  # remove non-phones
            seg = tier.elem[a]
            if (not seg.content) or (sym_i in seg.content):
                tier.pop(a)
        for a in range(len(ptier)-1,-1,-1):                 # add fillers
            pseg = ptier.elem[a]
            seg = tier.findTime(pseg.start+((pseg.end-pseg.start)/2))
            s_sym = sym if not re.search(sym_i,pseg.content) else pseg.content
            if seg and (seg.start >= pseg.start):
                continue
            i = 0 if not seg else seg.index()+1
            tier.create(i,"",pseg.start,pseg.end,s_sym)
    trans.renameSegs()                                      # segments IDs
    toPraat.toPraat(nf,trans)                               # save TextGrid
def ph_praat(aud_path,tgd_path,ph_path,sym_t,sym_i):
    """Calls the Praat script."""
    pr_d = os.path.abspath(os.path.join(PH_HOME,"script_anonym"))
    subprocess.run([os.path.join(pr_d,"Praat.exe"),'--new-send',
                    os.path.join(pr_d,"ph_ofrom.praat"),aud_path,tgd_path,
                    ph_path,sym_t,sym_i,"1"])
def find_pairs(d,nd,ad="",aud_ext=".wav"):
    """Generator for pairs of TextGrids and their audio file.
       The files should have the same name 'fi' and folder 'd'."""
    ad = d if not ad else ad    # audio path
    for file in os.listdir(d):
        fi,ext = os.path.splitext(file)
        tgd_path = os.path.join(d,file)
        aud_path = os.path.join(ad,fi+aud_ext)
        if (ext.lower() == ".textgrid") and (os.path.isfile(aud_path)):
            ph_path = os.path.join(nd,file)
            yield tgd_path,aud_path,ph_path
    # main function
def praatAlign(tgd_path,aud_path,ph_path,sym_t="[",sym_i="[_#@%]",
               ch_post=True):
    """Main function, calls 'ph_ofrom.praat' on a given file.
    ARGUMENTS:
    - tgd_path (str):   The input file (textgrid).
    - wav_path (str):   The input file (sound).
    - ph_path (str):    The output file.
    - sym_t (str):      A regex to eliminate tiers containing it.
    - sym_i (str):      A regex to eliminate segments containing it.
    - ch_clean (bool):  Whether to clean tiers and symbols.
    RETURNS:
    - Creates/overwrites a TextGrid file 'ph_path' with phonemic alignment.
    Pre/post-cleans the file (ch_clean/ch_post)."""
    ph_praat(aud_path,tgd_path,ph_path,sym_t,sym_i)
    post_align(ph_path,ph_path,sym_i,"_","?")
    if ch_post:
        post_clean(ph_path,ph_path)
def allPraatAlign(d,nd,ad="",sym_t="[",sym_i="[_#@%]",
                  aud_ext=".wav",ch_post=True):
    """Loop over a folder, calls 'praatAlign' for each file."""
    for tgd_path,aud_path,ph_path in find_pairs(d,nd,ad,aud_ext):
        praatAlign(tgd_path,aud_path,ph_path,sym_t,sym_i,ch_post)
def allPostClean(d,nd):
    """Iterates over each 'd' file, cleans the content, saves in 'nd'."""
    for file in os.listdir(d):
        fi,ext = os.path.splitext(file)
        if ext.lower() != ".textgrid":
            continue
        print(fi,end="\r")
        post_clean(os.path.join(d,file),os.path.join(nd,file))

if __name__ == "__main__":
    idir = ""
    odir = ""
    sym_t,sym_i,aud_ext,ch_post = "[\[/]","[_#@%]",".wav",True
    l_d = []
    for d in l_d:
        dp = ad = os.path.join(idir,d)
        ndp = os.path.join(odir,d)
        if not os.path.isdir(ndp):
            os.mkdir(ndp)
        # allPostClean(dp,ndp)
        allPraatAlign(dp,ndp,ad,sym_t,sym_i,aud_ext,ch_post)
    
    
    
