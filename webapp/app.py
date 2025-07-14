import io
import secrets

import numpy as np
import streamlit as st

from alcgen.configuration import RandomGuideConfiguration, DatasetConfiguration
from alcgen.generator import generate
from alcgen.random_guide import RandomGuide
from alcgen.syntax import to_manchester, to_pretty


def config(key_prefix: str, disabled: bool, closed: bool) -> RandomGuideConfiguration | None:
    min_n_conjuncts = 2 if closed else 1
    n_conjuncts = st.slider("Conjuncts count", min_value=min_n_conjuncts, max_value=10, value=(min_n_conjuncts, 3),
                            step=1, disabled=disabled,
                            key=f"{key_prefix}_n_conjuncts")
    p_disjuncts = st.slider("Disjuncts probability", min_value=0.0, max_value=1.0, step=0.1, disabled=disabled,
                            key=f"{key_prefix}_p_disjuncts")
    n_disjuncts = st.slider("Disjuncts count", min_value=2, max_value=10, value=(2, 2), step=1,
                            disabled=disabled or p_disjuncts <= 0.0, key=f"{key_prefix}_n_disjuncts")
    can_use_existential = depth > 0
    n_existential = st.slider("Existential restrictions count", min_value=0, max_value=10, value=(0, 3), step=1,
                              disabled=disabled or not can_use_existential, key=f"{key_prefix}_n_existential")
    n_roles = st.slider("Maximal number of roles", min_value=1, max_value=10, value=1, step=1,
                        disabled=disabled or not can_use_existential, key=f"{key_prefix}_n_roles")
    can_use_universal = can_use_existential and n_existential[1] > 0
    use_universals = st.checkbox("Universal restrictions", value=can_use_universal,
                                 disabled=disabled or not can_use_existential, key=f"{key_prefix}_use_universals")
    universal_th = st.slider("Universal restriction threshold", min_value=0,
                             max_value=n_existential[1] if use_universals else 1, step=1,
                             value=(min(2, n_existential[1]), min(2, n_existential[1])),
                             disabled=disabled or not use_universals,
                             key=f"{key_prefix}_universal_th")
    if not use_universals:
        universal_th = (None, None)
    if disabled:
        return None
    return RandomGuideConfiguration(conjuncts_low=n_conjuncts[0], conjuncts_high=n_conjuncts[1],
                                    disjuncts_p=p_disjuncts, disjuncts_low=n_disjuncts[0],
                                    disjuncts_high=n_disjuncts[1],
                                    n_roles=n_roles,
                                    existential_low=n_existential[0], existential_high=n_existential[1],
                                    universal_threshold_low=universal_th[0], universal_threshold_high=universal_th[1],
                                    )


st.title(r"$\mathcal{ALC}$ random formula generator")

depth = st.slider("ABox depth", min_value=0, max_value=10, step=1, value=2)
minimize = st.checkbox("Minimize the number of different atomic classes in the formula", value=True,
                       help="If left unchecked, a single atomic class will not appear twice in the resulting formula. If checked, some symbols may be repeated. The minimization process is heuristic and there is not guarantee that the final number of distinct atomic classes is minimal in any sense.")
close = st.checkbox("Make the formula unsatisfiable", value=True,
                    help="If checked, the resulting formula will be unsatisfiable. Otherwise, the formula will be satisfiable.")
seed = st.number_input("Random seed", min_value=0, max_value=(1 << 32) - 1, value=secrets.randbits(32), help="The seed to be used in the random number generator. The same seed with the same configuration will yield the same formula.")
prefix = st.text_input("Prefix (for OWL serialization)", value="http://example.com/alcgen#",
                       help=f"Prefix to be used in the OWL serialization. The generated class will be identified by the local name D.")

col1, col2 = st.columns(2)

with col1:
    st.checkbox("Basic configuration", value=True, disabled=True)
    base_config = config("base", False, close)
    use_universals = base_config.universal_threshold_low is not None and base_config.universal_threshold_high is not None

with col2:
    use_universal_config = st.checkbox("Use different parameters in universal restrictions", value=False,
                                       disabled=not use_universals)
    universal_config = config("universal", not use_universal_config, close)

st.download_button("Download config",
                   data=DatasetConfiguration(min_depth=depth, max_depth=depth, n_instances=1,
                                             save_open=not minimize and not close,
                                             save_open_minimized=minimize and not close,
                                             save_closed=not minimize and close,
                                             save_closed_minimized=minimize and close,
                                             seed_depth=0, seed_instance=0, seed_const=seed,
                                             prefix=prefix,
                                             guide=base_config,
                                             universal_guide=universal_config).model_dump_json(),
                   mime="application/json", file_name="config.json")

if st.button("Generate"):
    ce = generate(depth, RandomGuide(np.random.default_rng(seed), base_config, universal_config), close, minimize)
    st.text(to_pretty(ce))
    with io.StringIO() as f:
        to_manchester(ce, "http://examples.com/foo", f)
        st.download_button("Download", data=f.getvalue(), mime="text/plain", file_name="result.owl")
