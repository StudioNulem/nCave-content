"""Strict MyThes data prep. Never guesses at malformed record boundaries."""
from pathlib import Path
from collections import Counter
import re, hashlib, json, sys

MAX_BYTES=100*1024*1024
MAX_ROWS=8192
def read(path):
    b=path.read_bytes()
    if len(b)>MAX_BYTES or b'\0' in b: raise ValueError("Size or NUL")
    header,sep,rest=b.partition(b'\n')
    if not sep: raise ValueError("No charset header")
    header=header.removesuffix(b'\r')
    codec=header.decode('ascii')
    b.decode(codec,errors='strict')
    it=enumerate(rest.split(b'\n'),2)
    stat=Counter()
    groups={}
    empty=[]
    nlines=rest.count(b'\n')+int(not rest.endswith(b'\n'))
    longest_index_key=0
    for line,value in it:
        if line==nlines+2 and not value: break
        value=value.removesuffix(b'\r')
        m=re.fullmatch(rb'([^|]{0,180})\|([0-9]+)',value)
        if not m: raise ValueError(f"Invalid header line {line}: {value[:130]!r}")
        key,count=m[1],int(m[2])
        if not 1<=count<=MAX_ROWS:raise ValueError(f"Count {count} at {line}")
        stat['blocks']+=1
        stat['max_input_meanings']=max(stat['max_input_meanings'],count)
        rows=[]
        for _ in range(count):
            row_no,x=next(it,(None,None))
            if row_no is None or (row_no==nlines+2 and x==b''): raise ValueError(f"EOF at {line}")
            x=x.removesuffix(b'\r')
            if not x or len(x)>16380 or b'\r' in x:raise ValueError(f"Empty/oversize or CR in meaning row {row_no}")
            rows.append(x)
        if not key:
            stat['empty_blocks']+=1
            empty.extend(rows)
            continue
        if key in groups: stat['repeated_blocks']+=1
        groups.setdefault(key,[]).extend(rows)
        longest_index_key=max(longest_index_key,len(key))
    if not groups or len(groups)>500000: raise ValueError("Index entry cap")
    return header,groups,empty,dict(stat,max_key_bytes=longest_index_key)
def derive(source, dest, merge=True, preserve_unmodified=False):
    header,original,empty,stats=read(source)
    expected={k:(list(dict.fromkeys(rows)) if merge else rows) for k,rows in original.items()}
    if any(len(rows)>MAX_ROWS for rows in expected.values()):raise ValueError("Merged cap")
    if preserve_unmodified:
        assert not merge and not stats.get('repeated_blocks',0)
        dest.write_bytes(source.read_bytes())
    else:
        with dest.open('wb') as f:
            f.write(header+b'\n')
            for key, rows in expected.items():
                f.write(key+b'|'+str(len(rows)).encode('ascii')+b'\n')
                for row in rows:f.write(row+b'\n')
    after,actual,empty_after,_=read(dest)
    assert header==after and list(original)==list(actual)
    assert actual==expected and empty_after==(empty if preserve_unmodified else [])
    empty_unique=len(set(empty)-{x for rows in original.values() for x in rows})
    visible=Counter()
    for key, rows in actual.items():
        visible['max_meanings']=max(visible['max_meanings'],len(rows))
        if len(rows)>32:visible['over_32_groups']+=1
        for x in rows:
            fields=x.split(b'|')
            terms=fields[1:] if len(fields)>1 else fields
            if len(fields)==1:visible['no_separator_rows']+=1
            if not all(terms):visible['empty_term_rows']+=1
            if terms and terms[0]==b'' and len(terms)>1:visible['leading_empty_term_rows']+=1
            if len(terms)>100:visible['over_100_rows']+=1
        if any(len(x.split(b'|'))-1>100 for x in rows):visible['over_100_keys']+=1
    h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    return dict(stats,encoding=header.decode(),unique_entries=len(actual),
        empty_rows=len(empty),empty_rows_not_elsewhere=empty_unique,
        rows_before=sum(map(len,original.values())),rows_after=sum(map(len,actual.values())),
        duplicate_rows_removed=sum(map(len,original.values()))-sum(map(len,actual.values())),
        input_sha256=h(source),output_sha256=h(dest),**visible)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 derive_mythes.py source-original.dat derived.dat")
    print(json.dumps(derive(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
