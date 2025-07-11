package benchmarker.jfact

import benchmarker.MainBase
import org.semanticweb.owlapi.model.OWLOntology
import org.semanticweb.owlapi.reasoner.OWLReasoner
import uk.ac.manchester.cs.jfact.JFactFactory

class JFactMain : MainBase() {

    private val jfactFactory = JFactFactory()

    override fun factory(ontology: OWLOntology): OWLReasoner = jfactFactory.createReasoner(ontology)

    companion object {
        @JvmStatic
        fun main(args: Array<String>): Unit {
            JFactMain().run(args)
        }
    }
}