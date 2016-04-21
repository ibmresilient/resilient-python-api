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

using System.Collections.Generic;
using Newtonsoft.Json;

namespace Co3.Rest.Dto
{
    public class ConstDto
    {
        [JsonProperty("nist_attack_vectors")]
        public Dictionary<int, NistAttackVectorDto> NistAttackVectors { get; set; }

        [JsonProperty("period_types")]
        public List<string> PeriodTypes { get; set; }

        [JsonProperty("task_statuses")]
        public Dictionary<string, TaskStatusDto> TaskStatuses { get; set; }

        [JsonProperty("states")]
        public Dictionary<int, StateDto> States { get; set; }

        [JsonProperty("incident_statuses")]
        public Dictionary<string, IncidentStatusDto> IncidentStatuses { get; set; }

        [JsonProperty("harm_statuses")]
        public Dictionary<int, HarmStatusDto> HarmStatuses { get; set; }

        [JsonProperty("crime_statuses")]
        public Dictionary<int, CrimeStatusDto> CrimeStatuses { get; set; }

        [JsonProperty("regulators")]
        public Dictionary<int, RegulatorDto> Regulators { get; set; }

        [JsonProperty("industries")]
        public Dictionary<int, IndustryDto> Industries { get; set; }

        [JsonProperty("industry_regulators_map")]
        public Dictionary<int, List<int>> IndustryRegulatorsMap { get; set; }

        [JsonProperty("timeframes")]
        public Dictionary<int, TimeFrameDto> Timeframes { get; set; }

        [JsonProperty("data_types")]
        public Dictionary<int, DataTypeDto> DataTypes { get; set; }

        [JsonProperty("geos")]
        public Dictionary<int, GeoDto> Geos { get; set; }

        [JsonProperty("data_formats")]
        public Dictionary<int, DataFormatTypeDto> DataFormats { get; set; }

        [JsonProperty("artifact_types")]
        public List<IncidentArtifactTypeDto> ArtifactTypes { get; set; }

        [JsonProperty("actions_framework")]
        public ActionsFrameworkInfoDto ActionsFrameworkInfo { get; set; }

        [JsonProperty("max_attachment_mb")]
        public int MaxAttachmentMb { get; set; }

        [JsonProperty("input_types")]
        public Dictionary<string, InputTypeDto> InputTypes { get; set; }

        [JsonProperty("action_types")]
        public Dictionary<int, string> ActionTypes { get; set; }

        [JsonProperty("message_destination_types")]
        public Dictionary<int, string> DestinationTypes { get; set; }

        [JsonProperty("pivot")]
        public PivotConstDto PivotConstants { get; set; }

        [JsonProperty("time_units")]
        public List<TimeUnitDto> TimeUnits { get; set; }

        [JsonProperty("server_version")]
        public ServerVersionDto ServerVersion { get; set; }
    }
}
