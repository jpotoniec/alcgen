import pandas as pd
import seaborn as sns

variants = {
    'open': 'sat',
    'open_minimized': 'sat minimized',
    'closed': 'unsat',
    'closed_minimized': 'unsat minimized',
}

def main():
    dfs = []
    for prefix in ["baseline", "large_conjuncts", "large_disjuncts", "no_disjuncts", "no_universals"]:
        for reasoner in ["hermit", "pellet", "jfact", "elk"]:
            fn = f"{prefix}-{reasoner}.jsonl"
            df = pd.read_json(fn, lines=True)
            df['reasoner'] = reasoner
            df['dataset'] = prefix
            dfs.append(df)

    df = pd.concat(dfs)
    path = df['path'].str.split('/', regex=True, expand=True)
    df['variant'] = path[path.columns[-1]].str.replace('.owl', '').apply(lambda x: variants[x])
    df['depth'] = path[path.columns[-3]]
    df['instance'] = path[path.columns[-2]]
    tmp = df.groupby(['dataset', 'depth', 'reasoner', 'variant']).count()['times']
    for item in tmp[tmp < tmp.mode()[0]].index:
        df = df[~((df['dataset'] == item[0]) & (df['depth'] == item[1]) & (df['reasoner'] == item[2]) & (
                df['variant'] == item[3]))]
    df = df.explode("times")

    df = df[df['times'] > 0]

    #sns.set_context("paper")
    sns.set_theme("paper", "ticks", font_scale=.8)
    g = sns.catplot(
        data=df, x="depth", y="times", hue="reasoner",
        errorbar="ci", kind="point",
        linestyles=["solid", "dashed", "dotted", "dashdot"],
        col="variant",
        row="dataset",
        aspect=0.9,
        log_scale=(False, True),
        palette="inferno",
        legend_out=False,
        margin_titles=True,
        height=21 / 5 / 2.54,
        linewidth=1
        # capsize=.2
        # height=6,
    )
    g.set_titles(row_template="{row_name}", col_template="{col_name}")
    sns.move_legend(g, "center right", bbox_to_anchor=(0.95, 0.36))
    # g.set_xlabels("Depth")
    # g.set_ylabels("Time (ns), log-scale")
    g.set_xlabels("")
    g.set_ylabels("")
    g.fig.tight_layout()
    g.savefig(f"result.pdf", dpi=300)


if __name__ == "__main__":
    main()
