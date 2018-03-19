// See https://forums.aws.amazon.com/thread.jspa?messageID=673012&tstart=0#673012
// for an API Gateway template that's used to process input from Twilio for this script.
//
// The output from this script should be passed back at application/xml.

package doorcode

import org.json4s._
import org.json4s.jackson.JsonMethods._

case class TwilioEvent
(
  CallSid: String,
  AccountSid: String,
  From: String,
  To: String,
  CallStatus: String,
  ApiVersion: String,
  Direction: String,
  ForwardedFrom: Option[String],
  CallerName: Option[String],
  FromCity: Option[String], // The city of the caller.
  FromState: Option[String], //The state or province of the caller.
  FromZip: Option[String], //The postal code of the caller.
  FromCountry: Option[String], //The country of the caller.
  ToCity: Option[String], //The city of the called party.
  ToState: Option[String], //The state or province of the called party.
  ToZip: Option[String], //The postal code of the called party.
  ToCountry: Option[String], //The country of the called party.

  // SIP parameters not included

  // If <Gather> was used:
  Digits: Option[String] // The digits the caller pressed, excluding the finishOnKey digit if used.
)

class Main {
  import java.io.{InputStream, OutputStream, PrintStream}
  implicit val formats = DefaultFormats

  val WRAPPER = """<?xml version="1.0" encoding="UTF-8"?><Response><Pause length="2"/>%s</Response>"""
  val CODE = "81355"

  def main(input: InputStream, output: OutputStream): Unit = {
    val input_s = scala.io.Source.fromInputStream(input).mkString
    println("input:")
    println(input_s)
    val jsValue = parse(input_s)
    val event: TwilioEvent = jsValue.extract[TwilioEvent]

    val contents: String = event.Digits match {
      case None => "<Gather timeout=\"10\" finishOnKey=\"#\"><Say>Please enter a door code, followed by pound.</Say></Gather>"
      case Some(CODE) => """<Play digits="9999"/>"""
      case Some(digits) => s"<Say>Sorry, no matching code found. Got $digits</Say>"
    }
    val result = String.format(WRAPPER, contents)
    println("output:")
    println(result)
    output.write(result.getBytes("UTF-8"))
  }
}
