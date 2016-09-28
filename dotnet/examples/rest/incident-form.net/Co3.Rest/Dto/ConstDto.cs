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
    ///  This type contains constant information for the server.  This information is useful in translating names that the user sees to IDs that other REST API endpoints accept. For example, the incidentDTO has a property called crimestatus_id. The valid values are stored in crime_statuses. This information generally only changes for new releases of Co3.
    /// </summary>
    public class ConstDto
    {

        /// <summary>
        ///  A map of the possible NIST attack vector values.  The key portion of the map contains the IDs and the value portion contains a NISTAttackVectorDTO.
        /// These values come from NIST 800-61 (see
        /// http://csrc.nist.gov/publications/nistpubs/800-61rev2/SP800-61rev2.pdf
        /// ).
        /// See also:
        /// incidentDTO (nist_attack_vectors property)
        /// </summary>
        [JsonProperty("nist_attack_vectors")]
        public Dictionary<int, NISTAttackVectorDto> NistAttackVectors { get; set; }

        /// <summary>
        ///  An array of the possible period type values.  These values are used when retrieving data from the OrgStatisticsRESTresource (see the incidents_by_type_over_time and new_and_open_incidents endpoints).
        /// </summary>
        [JsonProperty("period_types")]
        public List<string> PeriodTypes { get; set; }

        /// <summary>
        ///  An array of the default wizard items and incident tabs represented by PredefinedViewItemDTOelements.
        /// </summary>
        [JsonProperty("predefined_items")]
        public List<PredefinedViewItemDto> PredefinedItems { get; set; }

        /// <summary>
        ///  A map of possible task statuses.  The key portion of the map is the task status code.  The value portion is a taskStatusDTO.
        /// See also:
        /// taskDTO (status property)
        /// </summary>
        [JsonProperty("task_statuses")]
        public Dictionary<string, TaskStatusDto> TaskStatuses { get; set; }

        /// <summary>
        ///  A map of possible US state values.  The key portion of the map is the ID of the state The value portion of the map is a stateDTO.
        /// Note that the ID for a given state is the same as it's geo ID.  See the
        /// geos property
        /// .
        /// </summary>
        [JsonProperty("states")]
        public Dictionary<int, StateDto> States { get; set; }

        /// <summary>
        ///  A map of possible incident statuses.  The key portion of the map contains the status code and the value portion is a incidentStatusDTO.
        /// See also:
        /// partialIncidentDTO (plan_status property)
        /// </summary>
        [JsonProperty("incident_statuses")]
        public Dictionary<string, IncidentStatusDto> IncidentStatuses { get; set; }

        /// <summary>
        ///  A map of possible harm status values.  The key portion of the map contains the ID of the harm status.  The value portion contains a harmStatusDTO
        /// See also:
        /// incidentPIIDTO (harmstatus_id property)
        /// </summary>
        [JsonProperty("harm_statuses")]
        public Dictionary<int, HarmStatusDto> HarmStatuses { get; set; }

        /// <summary>
        ///  A map of possible crime status values.  The key portion of the map contains the ID of the crime status.  The value portion contains a crimeStatusDTO.
        /// See also:
        /// incidentDTO (crimestatus_id property)
        /// </summary>
        [JsonProperty("crime_statuses")]
        public Dictionary<int, CrimeStatusDto> CrimeStatuses { get; set; }

        /// <summary>
        ///  A map of possible regulator values.  The key portion of the map contains the ID of the regulator.  The value portion contains a regulatorDTO.
        /// See also:
        /// regulatorsDTO
        /// .
        /// </summary>
        [JsonProperty("regulators")]
        public Dictionary<int, RegulatorDto> Regulators { get; set; }

        /// <summary>
        ///  A map of possible industry values.  The key portion of the map contains the ID of the industry.  The value portion contains an industryDTO.
        /// </summary>
        [JsonProperty("industries")]
        public Dictionary<int, IndustryDto> Industries { get; set; }

        /// <summary>
        ///  A map of industries to regulators.  These are regulators that apply for the specified industry.  The key of this map is the industry ID and the value is the regulator ID.  See also regulatorsand industries.
        /// </summary>
        [JsonProperty("industry_regulators_map")]
        public Dictionary<int, List<int>> IndustryRegulatorsMap { get; set; }

        /// <summary>
        ///  A map of possible timeframe values.  The key portion of the map contains the IDs and the value portion contains a timeframeDTO.
        /// </summary>
        [JsonProperty("timeframes")]
        public Dictionary<int, TimeframeDto> Timeframes { get; set; }

        /// <summary>
        ///  A map of possible data type values.  The key portion of the map contains the data type ID and the value portion contains a dataTypeDTO.
        /// See also:
        /// fullIncidentDataDTO (dtm property)
        /// </summary>
        [JsonProperty("data_types")]
        public Dictionary<int, DataTypeDto> DataTypes { get; set; }

        /// <summary>
        ///  A map of possible "geo" values.  A geo is short for geographical region.  It can be a region (such as Europe), country (such as United States) or a state/province (such as Massachusetts or Manitoba).  The ID portion of the map is the geo ID.  The value portion is a geoDTO.
        /// Geo IDs are specified in the
        /// incidentCountsDTO
        /// to indicate how many records have been lost for a particular state/province.
        /// Geo IDs are also used to specify the state and country properties of the
        /// incidentDTO
        /// .
        /// </summary>
        [JsonProperty("geos")]
        public Dictionary<int, GeoDto> Geos { get; set; }

        /// <summary>
        /// A map of possible data formats.  The following are examples of data formats: Paper Electronic Verbal
        /// The key portion of the map is the data format ID.  The value contains a
        /// dataFormatTypeDTO
        /// .
        /// See also:
        /// incidentPIIDTO (data_format property)
        /// .
        /// </summary>
        [JsonProperty("data_formats")]
        public Dictionary<int, DataFormatTypeDto> DataFormats { get; set; }

        /// <summary>
        ///  A list of possible artifact types.  See incidentArtifactTypeDTO.
        /// </summary>
        [JsonProperty("artifact_types")]
        public List<IncidentArtifactTypeDto> ArtifactTypes { get; set; }

        /// <summary>
        ///  Information about the actions framework.
        /// </summary>
        [JsonProperty("actions_framework")]
        public ActionsFrameworkInfoDto ActionsFrameworkInfo { get; set; }

        /// <summary>
        ///  The maximum allowed attachment size (in megabytes).
        /// </summary>
        [JsonProperty("max_attachment_mb")]
        public int MaxAttachmentMb { get; set; }

        /// <summary>
        ///  The maximum number of allowed artifacts to be loaded at same time.
        /// </summary>
        [JsonProperty("max_artifacts")]
        public int MaxArtifacts { get; set; }

        /// <summary>
        ///  A mapping of input type name to InputTypeDTO.  This map allows you to get information about input types in the system (e.g. what "methods" they support for conditions and the valid types to which a type can be transformed).
        /// </summary>
        [JsonProperty("input_types")]
        public Dictionary<string, InputTypeDto> InputTypes { get; set; }

        /// <summary>
        ///  The supported action type IDs and their names.  The key portion of the map is the ID.  The value portion is the display value.
        /// </summary>
        [JsonProperty("action_types")]
        public Dictionary<int, string> ActionTypes { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("message_destination_types")]
        public Dictionary<int, string> DestinationTypes { get; set; }

        /// <summary>
        ///  Get the constant data for pivoting services.
        /// See
        /// PivotConstDTO
        /// .
        /// </summary>
        [JsonProperty("pivot")]
        public PivotConstDto PivotConstants { get; set; }

        /// <summary>
        ///  A list of the supported time units for automatic tasks and system task overrides.
        /// </summary>
        [JsonProperty("time_units")]
        public List<TimeUnitDto> TimeUnits { get; set; }

        /// <summary>
        ///  The server version.
        /// </summary>
        [JsonProperty("server_version")]
        public ServerVersionDto ServerVersion { get; set; }

    }
}
