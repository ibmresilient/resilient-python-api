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
    ///  Contains information about a user.
    /// </summary>
    public class JustUserDto
    {

        /// <summary>
        ///  The user's ID.
        /// </summary>
        [JsonProperty("id")]
        public int Id { get; set; }

        /// <summary>
        ///  The user's first name.
        /// </summary>
        [JsonProperty("fname")]
        public string FirstName { get; set; }
        
        /// <summary>
        ///  The user's last name.
        /// </summary>
        [JsonProperty("lname")]
        public string LastName { get; set; }
        
        /// <summary>
        ///  The status of the user.  The following values are possible: 'A' - the user is active. 'I' - the user is inactive. 'P' - the user is pending activation (i.e. an invitation was created but not accepted by the user). 'R' - the user is being reset.
        /// </summary>
        [JsonProperty("status")]
        public JustUserStatus Status { get; set; }

        /// <summary>
        ///  User's email address.
        /// </summary>
        [JsonProperty("email")]
        public string Email { get; set; }

        /// <summary>
        ///  User's phone number.
        /// </summary>
        [JsonProperty("phone")]
        public string PhoneNumber { get; set; }
        
        /// <summary>
        ///  User's cell phone number.
        /// </summary>
        [JsonProperty("cell")]
        public string CellNumber { get; set; }
        
        /// <summary>
        ///  The user's job title (e.g. Incident Response Manager).
        /// </summary>
        [JsonProperty("title")]
        public string JobTitle { get; set; }

        /// <summary>
        ///  Notes about the user.
        /// </summary>
        [JsonProperty("notes")]
        public string Notes { get; set; }

        /// <summary>
        ///  The date of the user's last login.
        /// </summary>
        [JsonProperty("last_login")]
        public DateTime LastLogin { get; set; }

        /// <summary>
        ///  true if the user's account is locked, false otherwise.
        /// </summary>
        [JsonProperty("locked")]
        public bool Locked { get; set; }

        /// <summary>
        ///  true if the user's account is authenticated externally, false otherwise.
        /// </summary>
        [JsonProperty("is_external")]
        public bool IsExternal { get; set; }

    }
}
