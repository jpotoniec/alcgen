package benchmarker.pellet

import benchmarker.MainBase
import openllet.owlapi.PelletReasoner
import org.semanticweb.owlapi.model.OWLOntology
import org.semanticweb.owlapi.reasoner.BufferingMode
import org.semanticweb.owlapi.reasoner.OWLReasoner

class PelletMain : MainBase() {
    override fun factory(ontology: OWLOntology): OWLReasoner = PelletReasoner(ontology, BufferingMode.BUFFERING)

    companion object {
        @JvmStatic
        fun main(args: Array<String>): Unit {
            PelletMain().run(args)
        }
    }
}