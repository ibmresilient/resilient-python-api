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
    /// Summary description for IncidentDTO
    /// </summary>
    public class IncidentDto : PartialIncidentDto
    {
        [JsonProperty("vers")]
        public int Version { get; set; }

        [JsonProperty("addr")]
        public string Address { get; set; }

        [JsonProperty("city")]
        public string City { get; set; }

        [JsonProperty("creator_id")]
        public ObjectHandle CreatorId { get; set; }

        [JsonProperty("creator")]
        public JustUserDto Creator { get; set; }

        [JsonProperty("crimestatus_id")]
        public ObjectHandle CrimestatusId { get; set; }

        [JsonProperty("employee_involved")]
        public bool EmployeeInvolved { get; set; }

        [JsonProperty("end_date")]
        public DateTime EndDate { get; set; }

        [JsonProperty("exposure_dept_id")]
        public ObjectHandle ExposureDeptId { get; set; }

        [JsonProperty("exposure_individual_name")]
        public string ExposureIndividualName { get; set; }

        [JsonProperty("exposure_vendor_id")]
        public ObjectHandle ExposureVendorId { get; set; }

        [JsonProperty("incident_type_ids")]
        public List<ObjectHandle> IncidentTypeIds { get; set; }

        [JsonProperty("jurisdiction_name")]
        public string JurisdictionName { get; set; }

        [JsonProperty("jurisdiction_reg_id")]
        public int JurisdictionRegId { get; set; }

        [JsonProperty("reporter")]
        public string Reporter { get; set; }

        [JsonProperty("start_date")]
        public DateTime StartDate { get; set; }

        [JsonProperty("state")]
        public ObjectHandle State { get; set; }

        [JsonProperty("country")]
        public ObjectHandle Country { get; set; }

        [JsonProperty("zip")]
        public string Zip { get; set; }

        [JsonProperty("exposure")]
        public int Exposure { get; set; }

        [JsonProperty("org_id")]
        public int OrgId { get; set; }

        [JsonProperty("is_scenario")]
        public bool IsScenario { get; set; }

        [JsonProperty("members")]
        public List<ObjectHandle> Members { get; set; }

        [JsonProperty("negative_pr_likely")]
        public bool NegativePrLikely { get; set; }

        [JsonProperty("perms")]
        public IncidentPermsDto Perms { get; set; }

        [JsonProperty("confirmed")]
        public bool Confirmed { get; set; }

        [JsonProperty("task_changes")]
        public TaskChangeDto TaskChanges { get; set; }

        [JsonProperty("exposure_type_id")]
        public ObjectHandle ExposureTypeId { get; set; }

        [JsonProperty("assessment")]
        public string Assessment { get; set; }

        [JsonProperty("data_compromised")]
        public bool DataCompromised { get; set; }

        [JsonProperty("nist_attack_vectors")]
        public List<ObjectHandle> NistAttackVectors { get; set; }

        [JsonProperty("properties")]
        public Dictionary<string, object> Properties { get; set; }

        [JsonProperty("resolution_id")]
        public ObjectHandle ResolutionId { get; set; }

        [JsonProperty("resolution_summary")]
        public TextContentDto ResolutionSummary { get; set; }
    }
}
