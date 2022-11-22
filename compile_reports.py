import pandas as pd
import numpy as np
import glob
import datetime as dt
import argparse

def parse_date(f):
    prefix = f.split(".")[0]
    date = dt.datetime.strptime("-".join(prefix.split("-")[1:]), "%Y-%m-%d")
    return date

def read_group(gls):
    dfv = []
    for i,f in enumerate(sorted(glob.glob(gls))):
        date = parse_date(f)
        df = pd.read_csv(f,sep='\t')
        df['date'] = date
        df['num'] = i
        dfv.append(df)
    return pd.concat(dfv)

def argparser():
    parser = argparse.ArgumentParser(description="Compile and filter periodic reports and cladestats files to produce a set of high quality lineages for formal designation.")
    parser.add_argument("-i","--input",default='./',help="Path to a directory containing *report.tsv and *cladestats.txt files to compile. Defaults to the current directory")
    parser.add_argument("-g","--growth",default=0,type=float,help="Minimum mean periodic percentage change in the size of the lineage over the period after its first appearance. Default is 0, meaning lineages that shrink or remain static on average are filtered.")
    parser.add_argument("-e","--escape_change",default=0,type=float,help="Minimum gain of immune escape as estimated by Bloom DMS data. Default is 0 (no change to escape value).")
    parser.add_argument("-p","--persistence",default=0,type=int,help="Minimum number of consecutive trees since initial designation. Default 0 (new lineages in the final tree can be accepted).")
    parser.add_argument("-o","--output",default="compiled_report.tsv",help="Name the compiled output report tsv.")
    return parser.parse_args()

def main():
    args = argparser()
    rdf = read_group(args.input + "*report.tsv")
    cdf = read_group(args.input + "*cladestats.txt")
    slopes = cdf.set_index(['clade','num']).sort_index().groupby("clade").inclusive_count.pct_change().groupby(level=0).mean().to_dict()
    rdf['growth'] = rdf.proposed_sublineage.apply(lambda x:slopes.get(x,np.nan))
    maxnum = rdf.num.max()
    final = rdf[(rdf.net_escape_gain > args.escape_change) & (rdf.growth > args.growth) & (args.persistence > maxnum - rdf.num)]
    final.to_csv(args.output,sep='\t')

if __name__ == "__main__":
    main()