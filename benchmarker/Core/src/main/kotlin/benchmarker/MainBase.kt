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
        val times = HashMap<String, ArrayList<Duration?>>()
        repeat(reps) {
            for (ontologyFile in args.sliceArray(2..<args.size)) {
                val m = OWLManager.createOWLOntologyManager()
                val ontology = m.loadOntology(IRI.create(File(ontologyFile)))
                val cls = m.owlDataFactory.getOWLClass(clsIri)
                System.gc()
                val time = measureTime {
                    val reasoner: OWLReasoner = factory(ontology)
                    reasoner.isSatisfiable(cls)
                }
                times.computeIfAbsent(ontologyFile) { ArrayList() }.add(time)
            }
        }
        for ((ontologyFile, t) in times.entries)
            println(Json.encodeToString(Result(ontologyFile, t.map { it?.inWholeNanoseconds ?: -1 })))
    }
}
