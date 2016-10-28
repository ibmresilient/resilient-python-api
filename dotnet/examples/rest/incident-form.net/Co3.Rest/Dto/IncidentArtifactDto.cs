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
    ///  Contains information about an incident artifact.
    /// </summary>
    public class IncidentArtifactDto
    {

        /// <summary>
        ///  The artifact ID.
        /// </summary>
        [JsonProperty("id")]
        public int Id { get; set; }

        /// <summary>
        ///  The type of the artifact.  See constDTO.artifact_types for a list of all possible values.
        /// </summary>
        [JsonProperty("type")]
        public ObjectHandle Type { get; set; }

        /// <summary>
        ///  The value of the artifact.  This would be, for example, the IP address for an IP address artifact.  When adding artifacts, the value can include multiple whitespace-separated values in this text field if the artifact type's is_multi_aware flag is true (see constDTO.artifact_types)
        /// </summary>
        [JsonProperty("value")]
        public string Value { get; set; }

        /// <summary>
        ///  Gets the artifact's description.
        /// </summary>
        [JsonProperty("description")]
        public TextContentDto Description { get; set; }

        /// <summary>
        ///  Gets the creator of this artifact
        /// </summary>
        [JsonProperty("creator")]
        public JustUserDto Creator { get; set; }

        /// <summary>
        ///  Read-only field containing a list of all of the threat source hits for this artifact.
        /// </summary>
        [JsonProperty("hits")]
        public List<ThreatHitDto> Hits { get; set; }

        /// <summary>
        ///  The artifact attachment (null indicates that the artifact has no attachment).
        /// </summary>
        [JsonProperty("attachment")]
        public AttachmentDto Attachment { get; set; }

        /// <summary>
        ///  The parent artifact ID.
        /// </summary>
        [JsonProperty("parent_id")]
        public int ParentId { get; set; }

        /// <summary>
        ///  The incident ID.
        /// </summary>
        [JsonProperty("inc_id")]
        public int IncId { get; set; }

        /// <summary>
        ///  The incident name.
        /// </summary>
        [JsonProperty("inc_name")]
        public string IncName { get; set; }

        /// <summary>
        ///  The date/time the artifact was created.
        /// </summary>
        [JsonProperty("created")]
        public DateTime Created { get; set; }

        /// <summary>
        ///  The IDs of any threat sources that are still in the process of being checked for this artifact.
        /// </summary>
        [JsonProperty("pending_sources")]
        public List<ObjectHandle> PendingSources { get; set; }

        /// <summary>
        ///  The current user's read/write/delete permissions are.
        /// </summary>
        [JsonProperty("perms")]
        public IncidentArtifactPermsDto Perms { get; set; }

        /// <summary>
        ///  Additional artifact properties
        /// </summary>
        [JsonProperty("properties")]
        public List<IncidentArtifactPropertyDto> Properties { get; set; }

        /// <summary>
        ///  The location of the incident artifact
        /// </summary>
        [JsonProperty("location")]
        public IncidentArtifactLocationDto Location { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("whois")]
        public WhoisDto Whois { get; set; }

        /// <summary>
        ///  The list of actions available to the caller for execution.
        /// </summary>
        [JsonProperty("actions")]
        public List<ActionInfoDto> Actions { get; set; }

    }
}
