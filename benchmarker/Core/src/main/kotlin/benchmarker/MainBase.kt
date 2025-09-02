package benchmarker

import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.semanticweb.owlapi.apibinding.OWLManager
import org.semanticweb.owlapi.model.IRI
import org.semanticweb.owlapi.model.OWLOntology
import org.semanticweb.owlapi.reasoner.OWLReasoner
import java.io.File
import kotlin.time.Duration
import kotlin.time.measureTime

@Serializable
data class Result(val path: String, val times: List<Long>)

abstract class MainBase {

    abstract fun factory(ontology: OWLOntology): OWLReasoner

    fun run(args: Array<String>): Unit {
        val clsIri = IRI.create(args[0])
        val reps = args[1].toInt()
        for (ontologyFile in args.sliceArray(2..<args.size)) {
            val m = OWLManager.createOWLOntologyManager()
            val ontology = m.loadOntology(IRI.create(File(ontologyFile)))
            val cls = m.owlDataFactory.getOWLClass(clsIri)
            val times = ArrayList<Duration?>()
            repeat(reps) {
                System.gc()
                val time = measureTime {
                    val reasoner: OWLReasoner = factory(ontology)
                    reasoner.isSatisfiable(cls)
                }
                times.add(time)
            }
            println(Json.encodeToString(Result(ontologyFile, times.map { it?.inWholeNanoseconds ?: -1 })))
        }
    }
}
