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
    public class FullOrgDto
    {
        [JsonProperty("org_info")]
        public JustOrgDto OrgInfo { get; set; }

        [JsonProperty("us_enabled")]
        public bool UsRegulatorsEnabled { get; set; }

        [JsonProperty("canada_enabled")]
        public bool CanadaRegulatorsEnabled { get; set; }

        [JsonProperty("eu_enabled")]
        public bool EuRegulatorsEnabled { get; set; }

        [JsonProperty("actions_framework_enabled")]
        public bool ActionsFrameworkEnabled { get; set; }

        [JsonProperty("attachments_enabled")]
        public bool AttachmentsEnabled { get; set; }

        [JsonProperty("breach_enabled")]
        public bool BreachEnabled { get; set; }

        [JsonProperty("sir_enabled")]
        public bool SecurityIncidentEnabled { get; set; }

        [JsonProperty("threat_sources")]
        public Dictionary<int, ThreatSourceDto> ThreatSources { get; set; }

        [JsonProperty("phases")]
        public Dictionary<int, PhaseDto> Phases { get; set; }

        [JsonProperty("attachments_used_bytes")]
        public long AttachmentsUsedBytes { get; set; }

        [JsonProperty("users")]
        public Dictionary<int, UserDto> Users { get; set; }

        [JsonProperty("unknown_users")]
        public Dictionary<string, UserDto> UnknownUsers { get; set; }

        [JsonProperty("geos")]
        public Dictionary<int, OrgGeoDto> Geos { get; set; }

        [JsonProperty("groups")]
        public Dictionary<int, GroupDto> Groups { get; set; }

        [JsonProperty("data_sources")]
        public Dictionary<int, DataSourceDto> DataSources { get; set; }

        [JsonProperty("exposure_vendors")]
        public Dictionary<int, ExposureVendorDto> ExposureVendors { get; set; }

        [JsonProperty("exposure_departments")]
        public Dictionary<int, ExposureDepartmentDto> ExposureDepartments { get; set; }

        [JsonProperty("regs")]
        public Dictionary<int, bool> Regs { get; set; }

        [JsonProperty("properties")]
        public List<OrganizationPropertyDto> Properties { get; set; }

        [JsonProperty("incident_types")]
        public Dictionary<int, IncidentTypeDto> IncidentTypes { get; set; }

        [JsonProperty("id")]
        public int Id { get; set; }

        [JsonProperty("incident_severities")]
        public Dictionary<int, IncSeverityDto> IncidentSeverities { get; set; }

        [JsonProperty("task_categories")]
        public Dictionary<int, TaskCategoryDto> TaskCategories { get; set; }
    }
}
