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
    public class CommentDto
    {

        /// <summary>
        ///  The comment's ID.
        /// </summary>
        [JsonProperty("id")]
        public int Id { get; set; }

        /// <summary>
        ///  The ID of the parent comment (null for top-level comments).
        /// </summary>
        [JsonProperty("parent_id")]
        public int ParentId { get; set; }

        /// <summary>
        ///  The ID of the user who created the comment.  See the fullOrgDTO users propertyfor a list of possible user values.
        /// </summary>
        [JsonProperty("user_id")]
        public ObjectHandle UserId { get; set; }

        /// <summary>
        ///  The user's first name.
        /// </summary>
        [JsonProperty("user_fname")]
        public string UserFname { get; set; }

        /// <summary>
        ///  The user's last name.
        /// </summary>
        [JsonProperty("user_lname")]
        public string UserLname { get; set; }

        /// <summary>
        ///  The date the comment was created.
        /// </summary>
        [JsonProperty("create_date")]
        public DateTime CreateDate { get; set; }

        /// <summary>
        ///  The date the comment was modified.
        /// </summary>
        [JsonProperty("modify_date")]
        public DateTime ModifyDate { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("modify_user")]
        public ModifyUserDto ModifyUser { get; set; }

        /// <summary>
        ///  The comment text.
        /// </summary>
        [JsonProperty("text")]
        public TextContentDto Text { get; set; }

        /// <summary>
        ///  An array of children comment objects (these are "replies" to this comment).
        /// </summary>
        [JsonProperty("children")]
        public List<CommentDto> Children { get; set; }

        /// <summary>
        ///  An array of user IDs who are mentioned in this comment.  You mention a user in a comment by typing @User.  Note that the client populates this.  That is, the client will have to populate mentioned_users itself (the server does not currently parse the comment text to look for mentioned users).
        /// </summary>
        [JsonProperty("mentioned_users")]
        public List<ObjectHandle> MentionedUsers { get; set; }

        /// <summary>
        ///  An object that describes the current user's permissions on the comment object.
        /// </summary>
        [JsonProperty("comment_perms")]
        public CommentPermsDto CommentPerms { get; set; }

        /// <summary>
        ///  A flag indicating if the comment is deleted.  Generally comment objects are actually removed from the database when the user deletes them.  However, if the user deletes a parent comment the parent is just marked as deleted (and it's text is cleared).
        /// </summary>
        [JsonProperty("is_deleted")]
        public bool IsDeleted { get; set; }

        /// <summary>
        ///  The list of actions available to the caller for execution.
        /// </summary>
        [JsonProperty("actions")]
        public List<ActionInfoDto> Actions { get; set; }

    }
}
