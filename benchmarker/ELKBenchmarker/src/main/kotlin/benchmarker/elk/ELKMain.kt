package benchmarker.elk

import benchmarker.MainBase
import org.semanticweb.elk.owlapi.ElkReasonerFactory
import org.semanticweb.owlapi.model.OWLOntology
import org.semanticweb.owlapi.reasoner.OWLReasoner

class ELKMain : MainBase() {

    private val reasonerFactory = ElkReasonerFactory()

    override fun factory(ontology: OWLOntology): OWLReasoner = reasonerFactory.createReasoner(ontology)

    companion object {
        @JvmStatic
        fun main(args: Array<String>): Unit {
            ELKMain().run(args)
        }
    }
}