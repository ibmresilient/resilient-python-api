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
    ///  Contains the configuration data from an exported system Note that v24 exports may contain exposure_vendors, exposure_departments and data_source properties, but those were never actually populated.  We also no longer support them in v26+ (instead those values should get included as field values in the incident exposure_vendor_id, exposure_dept_id and data_source_ids fields).  We ignore them on import.
    /// </summary>
    public class ConfigurationExportDto
    {

        /// <summary>
        ///  The version number from which the import was generated.  If null, then it's a v24.x version that created it.
        /// </summary>
        [JsonProperty("server_version")]
        public ServerVersionDto ServerVersion { get; set; }

        /// <summary>
        ///  The file format version number.  If it's null, it means VERSION_1 because we didn't include it in the original release.
        /// </summary>
        [JsonProperty("export_format_version")]
        public int ExportFormatVersion { get; set; }

        /// <summary>
        ///  The internal ID of the exported configuration.
        /// </summary>
        [JsonProperty("id")]
        public int Id { get; set; }

        /// <summary>
        ///  The date the configuration was exported.
        /// </summary>
        [JsonProperty("export_date")]
        public DateTime ExportDate { get; set; }

        /// <summary>
        ///  The fields being exported. Will contain any incident-specific fields as well as action-specific fields if actions were part of the export.
        /// </summary>
        [JsonProperty("fields")]
        public List<FieldDefDto> Fields { get; set; }

        /// <summary>
        ///  The incident types being exported.
        /// </summary>
        [JsonProperty("incident_types")]
        public List<IncidentTypeDto> IncidentTypes { get; set; }

        /// <summary>
        ///  The phases being exported.
        /// </summary>
        [JsonProperty("phases")]
        public List<PhaseDto> Phases { get; set; }

        /// <summary>
        ///  The automatic tasks being exported.
        /// </summary>
        [JsonProperty("automatic_tasks")]
        public List<AutomaticTaskDto> AutomaticTasks { get; set; }

        /// <summary>
        ///  The system task overrides being exported.
        /// </summary>
        [JsonProperty("overrides")]
        public List<SystemTaskOverrideDto> Overrides { get; set; }

        /// <summary>
        ///  The message destinations being exported.
        /// </summary>
        [JsonProperty("message_destinations")]
        public List<MessageDestinationDto> MessageDestinations { get; set; }

        /// <summary>
        ///  The actions being exported. Contains both manual and automatic actions.
        /// </summary>
        [JsonProperty("actions")]
        public List<ActionDto> Actions { get; set; }

        /// <summary>
        ///  The layouts being exported. This includes the incident wizard, incident details view, incident close view.
        /// </summary>
        [JsonProperty("layouts")]
        public List<LayoutDto> Layouts { get; set; }

        /// <summary>
        ///  The notification definitions being exported.
        /// </summary>
        [JsonProperty("notifications")]
        public List<NotificationDefDto> Notifications { get; set; }

        /// <summary>
        ///  The organization timeframes being exported.
        /// </summary>
        [JsonProperty("timeframes")]
        public List<OrgTimeframeDto> Timeframes { get; set; }

        /// <summary>
        ///  The organization industries being exported.
        /// </summary>
        [JsonProperty("industries")]
        public OrgIndDto Industries { get; set; }

        /// <summary>
        ///  The organization regulators being exported.
        /// </summary>
        [JsonProperty("regulators")]
        public OrgRegDto Regulators { get; set; }

        /// <summary>
        ///  The organization data types being exported.
        /// </summary>
        [JsonProperty("data_types")]
        public OrgDataTypesDto DataTypes { get; set; }

        /// <summary>
        ///  The organization geos being exported.
        /// </summary>
        [JsonProperty("geos")]
        public OrgRegDto Geos { get; set; }

        /// <summary>
        ///  The task order being exported.
        /// </summary>
        [JsonProperty("task_order")]
        public List<string> TaskOrder { get; set; }

        /// <summary>
        ///  The custom types (currently only data tables) being exported.
        /// </summary>
        [JsonProperty("types")]
        public List<TypeDto> Types { get; set; }

    }
}
