package benchmarker.hermit

import benchmarker.MainBase
import org.semanticweb.HermiT.Configuration
import org.semanticweb.HermiT.Reasoner
import org.semanticweb.owlapi.model.OWLOntology
import org.semanticweb.owlapi.reasoner.OWLReasoner

class HermiTMain : MainBase() {
    override fun factory(ontology: OWLOntology): OWLReasoner = Reasoner(Configuration(), ontology)

    companion object {
        @JvmStatic
        fun main(args: Array<String>): Unit {
            HermiTMain().run(args)
        }
    }
}