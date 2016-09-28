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
    public class IncidentDto : PartialIncidentDto
    {

        /// <summary>
        ///  The version of the incident.  Note that if you attempt to save an incident and the vers field doesn't match the current version, you will get a 409 "conflict" HTTP error code. This is done so you don't overwrite another user's changes.
        /// </summary>
        [JsonProperty("vers")]
        public int Vers { get; set; }

        [Obsolete("Property has been renamed to Vers to be consistent with the API")]
        public int Version { get; set; }

        /// <summary>
        ///  The address where the incident occurred (e.g. 125 Main Street).
        /// </summary>
        [JsonProperty("addr")]
        public string Addr { get; set; }

        [Obsolete("Property has been renamed to Addr to be consistent with the API")]
        public string Address { get; set; }

        /// <summary>
        ///  The city where the incident occurred.
        /// </summary>
        [JsonProperty("city")]
        public string City { get; set; }

        /// <summary>
        ///  The ID of the user that created the incident.  This is a read-only property.
        /// </summary>
        [JsonProperty("creator_id")]
        public ObjectHandle CreatorId { get; set; }

        /// <summary>
        ///  A justUserDTO object that represents the creator.  This object will include the creator's email address, first name, last name, etc.
        /// </summary>
        [JsonProperty("creator")]
        public JustUserDto Creator { get; set; }

        /// <summary>
        ///  The ID of the crime status.  See also constDTO (crime_statuses property).
        /// </summary>
        [JsonProperty("crimestatus_id")]
        public ObjectHandle CrimestatusId { get; set; }

        /// <summary>
        ///  Was an employee involved?  true means that an employee was known to be involved.  false means that an employee was definitely not involved. A null value means that it is unknown whether an employee was involved.
        /// This value generally only applies if the "exposure type" is "individual". That is, if the incident was caused by an individual person.
        /// </summary>
        [JsonProperty("employee_involved")]
        public bool EmployeeInvolved { get; set; }

        /// <summary>
        ///  The date the incident was closed.  This is a read-only property.
        /// </summary>
        [JsonProperty("end_date")]
        public DateTime EndDate { get; set; }

        /// <summary>
        ///  The department within the company that the incident was related to.
        /// This value generally only applies if the "exposure type" is "individual". That is, if the incident was caused by an individual person.
        /// </summary>
        [JsonProperty("exposure_dept_id")]
        public ObjectHandle ExposureDeptId { get; set; }

        /// <summary>
        ///  The free-form text name of the individual who caused the incident.  For example, if Mary Jones lost her laptop then you would set the exposure_individual_name to "Mary Jones".
        /// This value generally only applies if the "exposure type" is "individual". That is, if the incident was caused by an individual person.
        /// </summary>
        [JsonProperty("exposure_individual_name")]
        public string ExposureIndividualName { get; set; }

        /// <summary>
        ///  The vendor who caused the incident.
        /// This value generally only applies if the "exposure type" is "external party". That is, if the incident was caused by an external party.
        /// </summary>
        [JsonProperty("exposure_vendor_id")]
        public ObjectHandle ExposureVendorId { get; set; }

        /// <summary>
        ///  The IDs of the incident types.  An incident type is something like Malware, Phishing, etc.
        /// The list of possible incident types and their ID values can be retrieved using the
        /// OrgREST
        /// resource (perform a GET on the /rest/orgs/{orgId} endpoint), which will return a
        /// fullOrgDTO
        /// object.  This object has an
        /// incident_types
        /// property that will contain the valid values.
        /// </summary>
        [JsonProperty("incident_type_ids")]
        public List<ObjectHandle> IncidentTypeIds { get; set; }

        /// <summary>
        ///  If this incident was a crime then this property indicates whereit was a crime.
        /// </summary>
        [JsonProperty("jurisdiction_name")]
        public string JurisdictionName { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("jurisdiction_reg_id")]
        public int JurisdictionRegId { get; set; }

        /// <summary>
        ///  Free form text field indicating who reported the incident.
        /// </summary>
        [JsonProperty("reporter")]
        public string Reporter { get; set; }

        /// <summary>
        ///  The date the incident occurred.
        /// </summary>
        [JsonProperty("start_date")]
        public DateTime StartDate { get; set; }

        /// <summary>
        ///  The state where the incident occurred.  This is a geo ID. See constDTO (states property)for the possible values.
        /// </summary>
        [JsonProperty("state")]
        public ObjectHandle State { get; set; }

        /// <summary>
        ///  The country where the incident occurred.  This is a geo ID. See constDTO (geos property)for the possible values.
        /// </summary>
        [JsonProperty("country")]
        public ObjectHandle Country { get; set; }

        /// <summary>
        ///  The ZIP/postal code where the incident occurred.
        /// </summary>
        [JsonProperty("zip")]
        public string Zip { get; set; }

        /// <summary>
        ///  The total amount of money (in US dollars) that you could be fined if you ignore this incident.  This is calculated by the Co3 rules engine based on the information that you provided.
        /// This is a readonly property.
        /// </summary>
        [JsonProperty("exposure")]
        public int Exposure { get; set; }

        /// <summary>
        ///  The ID of the organization where the incident resides.
        /// This is a readonly property.
        /// </summary>
        [JsonProperty("org_id")]
        public int OrgId { get; set; }

        /// <summary>
        ///  true if the incident is to be run as a what-if scenario.  In this case the incident is not saved to the database, but it's assessment property is set and (if want_full_data was requested) the fullIncidentDataDTO tasks propertyis set.
        /// Setting this value to false will cause an incident to be created.
        /// </summary>
        [JsonProperty("is_scenario")]
        public bool IsScenario { get; set; }

        /// <summary>
        ///  The list of member user IDs.
        /// The list of users is available in the
        /// fullOrgDTO (users property)
        /// .
        /// </summary>
        [JsonProperty("members")]
        public List<ObjectHandle> Members { get; set; }

        /// <summary>
        ///  Is a negative "public relations" (PR) response likely because of this incident?  true indicates that a negative PR response is likely.  false indicates that a negative PR response is unlikely. A null value means that you do not know if a negative PR value is likely or unlikely.
        /// </summary>
        [JsonProperty("negative_pr_likely")]
        public bool NegativePrLikely { get; set; }

        /// <summary>
        ///  Indicates that the current user's permissions are to various elements of the incident.  For example, is the current user allowed to change the membership of the incident (stored in the change_members property of the returned object).
        /// </summary>
        [JsonProperty("perms")]
        public IncidentPermsDto Perms { get; set; }

        /// <summary>
        ///  Is the incident confirmed?  Specify true if you're sure this is an incident.  Specify false if you're not yet sure.  As an example, consider the case where a SIEM system reports suspicious activity that you want to investigate.  The automatic entry of the incident would set confirmed = false.  Once a human investigates and determines that an incident actually occurred, the user would set this field to true through the Co3 UI.
        /// </summary>
        [JsonProperty("confirmed")]
        public bool Confirmed { get; set; }

        /// <summary>
        ///  Gets information about what tasks were added or removed by the previous PUT operation.  This only applies for PUT operations where the incident has changed causing an automatic change to one or more tasks.
        /// This is a readonly property.
        /// </summary>
        [JsonProperty("task_changes")]
        public TaskChangeDto TaskChanges { get; set; }

        /// <summary>
        ///  The exposure type for the incident.  This is used to track the origin of the exposure. For example, was the origin of the incident an "individual" or "external party".
        /// </summary>
        [JsonProperty("exposure_type_id")]
        public ObjectHandle ExposureTypeId { get; set; }

        /// <summary>
        ///  An XML text string describing the high-level assessment of the incident.
        /// This is a readonly property.
        /// </summary>
        [JsonProperty("assessment")]
        public string Assessment { get; set; }

        /// <summary>
        ///  Has data been compromised because of the incident?  Specify true to indicate that data was definitely compromised.  Specify false to indicate that data was definitely not compromised.  Specify a null value to indicate that you do not yet know if data was compromised (a task will be created to get you to investigate.)
        /// </summary>
        [JsonProperty("data_compromised")]
        public bool DataCompromised { get; set; }

        /// <summary>
        ///  A list of IDs of all of the NIST attack vectors that apply.
        /// These values come from NIST 800-61 (see
        /// http://csrc.nist.gov/publications/nistpubs/800-61rev2/SP800-61rev2.pdf
        /// ).
        /// Note that the IDs specified here are internal Co3 IDs.  The list of IDs is available in the
        /// constDTO (nist_attack_vectors property)
        /// .
        /// </summary>
        [JsonProperty("nist_attack_vectors")]
        public List<ObjectHandle> NistAttackVectors { get; set; }

        /// <summary>
        ///  The custom properties (fields) for this incident.  Use this to set/get custom properties for the incident.  For example, if you have a custom field called moon_phase then you would set/get it's value using incident.properties.moon_phase.
        /// </summary>
        [JsonProperty("properties")]
        public Dictionary<string, object> Properties { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("resolution_id")]
        public ObjectHandle ResolutionId { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("resolution_summary")]
        public TextContentDto ResolutionSummary { get; set; }

        /// <summary>
        ///  The incidentPIIDTOfor the incident. This contains information about privacy breaches.
        /// </summary>
        [JsonProperty("pii")]
        public IncidentPIIDto Pii { get; set; }

    }
}
