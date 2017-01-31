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
    ///  Class to represent data sent for the creation of events (POST /rest/incidents).
    /// </summary>
    public class FullIncidentDataDto : IncidentDto
    {

        /// <summary>
        ///  The incidentDataTypesDTOfor the incident. This contains information about the types of data that were lost (e.g First Name, Last Name, Credit card number, etc.).
        /// </summary>
        [JsonProperty("dtm")]
        [JsonConverter(typeof(JsonConverters.ObjectHandleKeyConverter<bool>))]
        public Dictionary<ObjectHandle, bool> Dtm { get; set; }

        /// <summary>
        ///  The incidentCountsDTOfor the incident. This contains information about the counts of records that were lost for the different geographical regions.
        /// </summary>
        [JsonProperty("cm")]
        public IncidentCountsDto Cm { get; set; }

        /// <summary>
        ///  The regulatorsDTOfor the incident. This contains information about the regulators that are in effect for the incident.  Note that the ids property of the regulatorsDTO contains non-state/province regulators.  So for example, you'd include the ID of the "GLB Act" regulator here.  State regulators will be used if record counts are specified for that state.
        /// </summary>
        [JsonProperty("regulators")]
        public RegulatorsDto Regulators { get; set; }

        /// <summary>
        ///  The HIPAARiskDTOfor the incident. This contains information required by HIPAA.  If HIPAA does not apply to this incident then the hipaa propert can be empty.
        /// </summary>
        [JsonProperty("hipaa")]
        public HipaaRiskDto Hipaa { get; set; }

        /// <summary>
        ///  Gets the list of tasks for the incident.  This data is not accepted on a POST or PUT.  It is only used if want_full_data=true is specified when the incident is created.  See also taskDTO.
        /// </summary>
        [JsonProperty("tasks")]
        public List<TaskDto> Tasks { get; set; }

        /// <summary>
        ///  Gets the list of artifacts for the incident. This data is accepted on a POST but not currently on PUT, but it should be in the future.
        /// </summary>
        [JsonProperty("artifacts")]
        public List<IncidentArtifactDto> Artifacts { get; set; }

        /// <summary>
        ///  Set some notes for the incident. This data is accepted on a POST but not currently on PUT, but it should be in the future.
        /// </summary>
        [JsonProperty("comments")]
        public List<IncidentCommentDto> Comments { get; set; }

        /// <summary>
        ///  The list of actions available to the caller for execution.
        /// </summary>
        [JsonProperty("actions")]
        public List<ActionInfoDto> Actions { get; set; }

    }
}
