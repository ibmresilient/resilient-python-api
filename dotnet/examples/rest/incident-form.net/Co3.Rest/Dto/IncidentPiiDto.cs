/*
 * Resilient Systems, Inc. ("Resilient") is willing to license software
 * or access to software to the company or entity that will be using or
 * accessing the software and documentation and that you represent as
 * an employee or authorized agent ("you" or "your") only on the condition
 * that you accept all of the terms of this license agreement.
 *
 * The software and documentation within Resilient's Development Kit are
 * copyrighted by and contain confidential information of Resilient. By
 * accessing and/or using this software and documentation, you agree that
 * while you may make derivative works of them, you:
 *
 * 1)  will not use the software and documentation or any derivative
 *     works for anything but your internal business purposes in
 *     conjunction your licensed used of Resilient's software, nor
 * 2)  provide or disclose the software and documentation or any
 *     derivative works to any third party.
 *
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace Co3.Rest.Dto
{
    /// <summary>
    /// </summary>
    public class IncidentPIIDto
    {

        /// <summary>
        ///  Whether sensitive or personal data was foreseeably exposed and/or compromised. A value of true or null ("Unknown") indicate that a breach response may be required.
        /// true means that data was compromised.  false means that data definitely was not compromised. null means that you don't know.
        /// </summary>
        [JsonProperty("data_compromised")]
        public bool DataCompromised { get; set; }

        /// <summary>
        ///  The harm status of the incident.  The possible values are specified in the constDTO harm_statuses property.
        /// </summary>
        [JsonProperty("harmstatus_id")]
        public ObjectHandle HarmstatusId { get; set; }

        /// <summary>
        ///  Was the that was lost encrypted?  true means that the data was encrypted; false means that it was not encrypted; null means that you do not know if data was encrypted.
        /// </summary>
        [JsonProperty("data_encrypted")]
        public bool DataEncrypted { get; set; }

        /// <summary>
        ///  Was the data contained and the exposure resolved?  true means that the exposure has been resolved; false means that it has not been resolved; null means that you do not know if it has been resolved.
        /// </summary>
        [JsonProperty("data_contained")]
        public bool DataContained { get; set; }

        /// <summary>
        ///  An array of data source IDs for the incident.  These values are configured specifically for your organization.
        /// </summary>
        [JsonProperty("data_source_ids")]
        public List<ObjectHandle> DataSourceIds { get; set; }

        /// <summary>
        ///  The format the data was in (e.g. Paper, Electronic or Verbal).  The possible values are available in the constDTO data_formats property.
        /// </summary>
        [JsonProperty("data_format")]
        public ObjectHandle DataFormat { get; set; }

        /// <summary>
        ///  An XML text string describing the high-level assessment of the incident. This is a readonly property.
        /// </summary>
        [JsonProperty("assessment")]
        public string Assessment { get; set; }

        /// <summary>
        ///  The total amount of money (in US dollars) that you could be fined if you ignore this incident.  This is calculated by the Co3 rules engine based on the information that you provided.
        /// This is a readonly property.
        /// </summary>
        [JsonProperty("exposure")]
        public int Exposure { get; set; }

    }
}
