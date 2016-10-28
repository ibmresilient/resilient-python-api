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
    ///  Represents an incident type in the system (e.g. Malware, Phishing, etc.).
    /// </summary>
    public class IncidentTypeDto
    {

        /// <summary>
        ///  The ID of the incident type.
        /// </summary>
        [JsonProperty("id")]
        public int Id { get; set; }

        /// <summary>
        ///  Is the incident type enabled?
        /// </summary>
        [JsonProperty("enabled")]
        public bool Enabled { get; set; }

        /// <summary>
        ///  The name of the incident type (e.g. "Malware").
        /// </summary>
        [JsonProperty("name")]
        public string Name { get; set; }

        /// <summary>
        ///  A description of the incident type.
        /// </summary>
        [JsonProperty("description")]
        public string Description { get; set; }

        /// <summary>
        ///  The date the incident type was created.
        /// </summary>
        [JsonProperty("create_date")]
        public DateTime CreateDate { get; set; }

        /// <summary>
        ///  The date the incident type was last updated.
        /// </summary>
        [JsonProperty("update_date")]
        public DateTime UpdateDate { get; set; }

        /// <summary>
        ///  The ID of the parent incident type.  Incident types can "inherit" from other incident types.  For example, you might have an incident type called "Lost Laptop" that will have various automatic tasks associated with it (like "Buy a new laptop for the employee").  You might have another incident type that inherits from this called "Lost Executive Laptop" that would have additional tasks associated with it.
        /// </summary>
        [JsonProperty("parent_id")]
        public ObjectHandle ParentId { get; set; }

        /// <summary>
        ///  Is the incident type to be hidden from view when creating incidents?
        /// </summary>
        [JsonProperty("hidden")]
        public bool Hidden { get; set; }

        /// <summary>
        ///  Is this a system-defined incident type?
        /// </summary>
        [JsonProperty("system")]
        public bool System { get; set; }

        /// <summary>
        ///  The UUID for this incident type
        /// </summary>
        [JsonProperty("uuid")]
        public string Uuid { get; set; }

        /// <summary>
        ///  This value is used for export/import to uniquely represent this incident type
        /// </summary>
        [JsonProperty("export_key")]
        public string ExportKey { get; set; }

    }
}
