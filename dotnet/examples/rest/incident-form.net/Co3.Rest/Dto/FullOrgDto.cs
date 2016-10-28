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
    public class FullOrgDto
    {

        /// <summary>
        ///  General information about the organization.
        /// </summary>
        [JsonProperty("org_info")]
        public JustOrgDto OrgInfo { get; set; }

        /// <summary>
        ///  Does the license enable US regulators?
        /// </summary>
        [JsonProperty("us_enabled")]
        public bool UsEnabled { get; set; }

        /// <summary>
        ///  Does the license enable Canada regulators?
        /// </summary>
        [JsonProperty("canada_enabled")]
        public bool CanadaEnabled { get; set; }

        /// <summary>
        ///  Does the license enable EU regulators?
        /// </summary>
        [JsonProperty("eu_enabled")]
        public bool EuEnabled { get; set; }

        /// <summary>
        ///  Indicates whether the org has enabled and is allowed to use the actions framework.
        /// </summary>
        [JsonProperty("actions_framework_enabled")]
        public bool ActionsFrameworkEnabled { get; set; }

        /// <summary>
        ///  Can attachments be added to tasks and incidents for this org?
        /// </summary>
        [JsonProperty("attachments_enabled")]
        public bool AttachmentsEnabled { get; set; }

        /// <summary>
        ///  Is the breach/privacy module enabled?
        /// </summary>
        [JsonProperty("breach_enabled")]
        public bool BreachEnabled { get; set; }

        /// <summary>
        ///  Is the security module enabled?
        /// </summary>
        [JsonProperty("sir_enabled")]
        public bool SirEnabled { get; set; }

        /// <summary>
        ///  A map of threat sources for this organization.  All threat sources that Co3 supports are included in this list.  The "enabled" property will be set to false if it is not enabled for this organization. See threatSourceDTO.
        /// The key portion of the map contains the ID of the threat source.  The value portion of the map contains the
        /// threatSourceDTO
        /// </summary>
        [JsonProperty("threat_sources")]
        public Dictionary<int, ThreatSourceDto> ThreatSources { get; set; }

        /// <summary>
        ///  A map of all the possible incident phases.  The ID portion of the map contains the ID of the phase.  The value portion contains the phaseDTO.
        /// </summary>
        [JsonProperty("phases")]
        public Dictionary<int, PhaseDto> Phases { get; set; }

        /// <summary>
        ///  The number of bytes the organization is currently using for attachment storage.
        /// </summary>
        [JsonProperty("attachments_used_bytes")]
        public long AttachmentsUsedBytes { get; set; }

        /// <summary>
        ///  Gets a user ID to userDTOmap.  This allows the caller to map the ID values returned by other APIs to user names.
        /// </summary>
        [JsonProperty("users")]
        public Dictionary<int, UserDto> Users { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("unknown_users")]
        public Dictionary<string, UserDto> UnknownUsers { get; set; }

        /// <summary>
        ///  A map of geo ID to orgGeoDTO.  This identifies jurisdictions (geos) the company conducts business and/or has customer data.
        /// </summary>
        [JsonProperty("geos")]
        public Dictionary<int, OrgGeoDto> Geos { get; set; }

        /// <summary>
        ///  A map of group ID to groupDTO.  This map contains all of the groups defined in the organization.
        /// </summary>
        [JsonProperty("groups")]
        public Dictionary<int, GroupDto> Groups { get; set; }

        /// <summary>
        ///  A map of regulator ID to boolean values that indicates which regulators are enabled by default for the organization.
        /// </summary>
        [JsonProperty("regs")]
        public Dictionary<int, bool> Regs { get; set; }

        /// <summary>
        ///  An array of organization properties.  These are general purpose properties associated with the organization.
        /// </summary>
        [JsonProperty("properties")]
        public List<OrganizationPropertyDto> Properties { get; set; }

        /// <summary>
        ///  A map of incident type ID incidentTypeDTO.  This is the list of incident types defined for the organization.
        /// See also
        /// incidentDTO incident_type_ids property
        /// .
        /// </summary>
        [JsonProperty("incident_types")]
        public Dictionary<int, IncidentTypeDto> IncidentTypes { get; set; }

        /// <summary>
        ///  The organization ID.
        /// </summary>
        [JsonProperty("id")]
        public int Id { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("incident_severities")]
        public Dictionary<int, IncSeverityDto> IncidentSeverities { get; set; }

        /// <summary>
        ///  A map of all the possible task categories.  The ID portion of the map contains the ID of the category.  The value portion contains the taskCategoryDTO.
        /// </summary>
        [JsonProperty("task_categories")]
        public Dictionary<int, TaskCategoryDto> TaskCategories { get; set; }
    }
}
