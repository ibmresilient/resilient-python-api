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
    ///  Holds information sent to a message destination when an action fires.
    /// </summary>
    public class ActionDataDto
    {

        /// <summary>
        ///  The ID of the action that triggered.
        /// </summary>
        [JsonProperty("action_id")]
        public int ActionId { get; set; }

        /// <summary>
        ///  The type of the object contained in the data.
        /// </summary>
        [JsonProperty("object_type")]
        public int ObjectType { get; set; }

        /// <summary>
        ///  Gets the incident data.
        /// </summary>
        [JsonProperty("incident")]
        public FullIncidentDataDto Incident { get; set; }

        /// <summary>
        ///  Gets the task data.  Note that this will be null if the action does not apply to tasks.  You can use the 'incident' property to get information about the task's incident.
        /// </summary>
        [JsonProperty("task")]
        public TaskDto Task { get; set; }

        /// <summary>
        ///  Gets the artifact data.  Note that this will be null if the action does not apply to artifacts.  You can use the 'incident' property to get information about the artifact's incident.
        /// </summary>
        [JsonProperty("artifact")]
        public IncidentArtifactDto Artifact { get; set; }

        /// <summary>
        ///  Gets the note data.  This will be null if the action does not apply to notes.  You can use the 'incident' property to get information about the note's incident.  If the not applies to a task, you can also use the 'task' property to get information about the note's task.
        /// </summary>
        [JsonProperty("note")]
        public CommentDto Note { get; set; }

        /// <summary>
        ///  Gets the milestone data.  This will be null if the action does not apply to milestones.  You can use the 'incident' property to get information about the milestone's incident.
        /// </summary>
        [JsonProperty("milestone")]
        public MilestoneDto Milestone { get; set; }

        /// <summary>
        ///  Gets the attachment data.  This will be null if the action does not apply to attachments.  You can use the 'incident' property to get information about the incident associated with the attachment.  You can use the 'task' property to get information about the task that the attachment is associated with (if the attachment applied to a task).
        /// </summary>
        [JsonProperty("attachment")]
        public AttachmentDto Attachment { get; set; }

        /// <summary>
        ///  Gets the row data of a data table.  This will be null if the action does not apply to data table rows.  You can use the 'incident' property to get information about the incident associated with the data table.
        /// </summary>
        [JsonProperty("row")]
        public DataTableRowDataDto Row { get; set; }

        /// <summary>
        ///  Gets information about the types.  Note that type_info only includes information relevant to this action data.  For example, it does NOT include field data values that are not referenced.
        /// </summary>
        [JsonProperty("type_info")]
        public Dictionary<String, ActionSimpleTypeDto> TypeInfo { get; set; }

        /// <summary>
        ///  Gets the custom properties (fields) associated with this action. This is only applicable for manual actions. This may be null if it is the result of an automatic action or a manual action without custom properties.
        /// </summary>
        [JsonProperty("properties")]
        public Dictionary<string, object> Properties { get; set; }

        /// <summary>
        ///  The user that triggered the action
        /// </summary>
        [JsonProperty("user")]
        public JustUserDto User { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("operation_type")]
        public OperationType OperationType { get; set; }

    }
}
