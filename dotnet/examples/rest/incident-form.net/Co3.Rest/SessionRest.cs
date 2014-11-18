/*
 * Co3 Systems, Inc. ("Co3") is willing to license software or access to 
 * software to the company or entity that will be using or accessing the 
 * software and documentation and that you represent as an employee or 
 * authorized agent ("you" or "your" only on the condition that you 
 * accept all of the terms of this license agreement.
 *
 * The software and documentation within Co3's Development Kit are 
 * copyrighted by and contain confidential information of Co3. By 
 * accessing and/or using this software and documentation, you agree 
 * that while you may make derivative works of them, you:
 * 
 * 1)   will not use the software and documentation or any derivative 
 *      works for anything but your internal business purposes in 
 *      conjunction your licensed used of Co3's software, nor
 * 2)   provide or disclose the software and documentation or any 
 *      derivative works to any third party.
 * 
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS 
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
 * ARE DISCLAIMED. IN NO EVENT SHALL CO3 BE LIABLE FOR ANY DIRECT, 
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED 
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

using Co3.Rest.Dto;

namespace Co3.Rest
{
    public class SessionRest : RestEndpoint
    {
        public const string EndPoint = "/session";

        public SessionRest() : base(null)
        {
        }

        public UserSessionDto Authenticate(AuthenticationDto credentials)
        {
            m_session = HttpPost<UserSessionDto>(EndPoint,
                credentials);
            return m_session;
        }

        public void LogOut()
        {
            HttpDelete<UserSessionDto>(EndPoint);
        }

        public OrgRest GetOrgRest()
        {
            return new OrgRest(this);
        }

        public ConstRest GetConstRest()
        {
            return new ConstRest(this);
        }

        public IncidentRest GetIncidentRest()
        {
            return new IncidentRest(this);
        }

        public FieldRest GetFieldRest()
        {
            return new FieldRest(this);
        }
    }
}
