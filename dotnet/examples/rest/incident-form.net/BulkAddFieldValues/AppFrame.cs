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
using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Forms;
using Co3.Rest;
using Co3.Rest.Dto;

namespace BulkAddFieldValues
{
    public partial class AppFrame : Form
    {
        private SessionRest m_sessionRest;
        private UserSessionDto m_session;

        public AppFrame()
        {
            InitializeComponent();

            m_sessionRest = null;

            ApiUrl.Text = RestEndpoint.Co3ApiUrl;
            UserEmail.Text = System.Configuration.ConfigurationManager.AppSettings["Email"];
        }

        private bool HasCredentials
        {
            get
            {
                return !string.IsNullOrEmpty(ApiUrl.Text)
                    && !string.IsNullOrEmpty(ApiUrl.Text.Trim())
                    && !string.IsNullOrEmpty(UserEmail.Text)
                    && !string.IsNullOrEmpty(UserEmail.Text.Trim())
                    && !string.IsNullOrEmpty(Password.Text);
            }
        }

        private void OnCredentialsChanged(object sender, EventArgs e)
        {
            ConnectBtn.Enabled = HasCredentials;   
        }

        private void ConnectBtn_Click(object sender, EventArgs e)
        {
            RestEndpoint.Co3ApiUrl = ApiUrl.Text.Trim();
            AuthenticationDto credentials = new AuthenticationDto()
            {
                Email = UserEmail.Text.Trim(),
                Password = Password.Text
            };

            m_sessionRest = new SessionRest();
            try
            {
                m_session = m_sessionRest.Authenticate(credentials);
                if (m_session == null)
                    return;
            }
            catch
            {
                MessageBox.Show("Invalid user credentials or API URL",
                    "Authentication Error", MessageBoxButtons.OK);
                return;
            }

            Orgs.Items.Clear();
            for (int i = 0; i < m_session.Orgs.Count; ++i)
            {
                Orgs.Items.Add(m_session.Orgs[i]);
            }

            Orgs.SelectedIndex = 0;
            Orgs_SelectedIndexChanged(sender, e);

            Orgs.Enabled = true;
            FieldNames.Enabled = true;
            ValuesFile.Enabled = true;
            BrowseBtn.Enabled = true;
            OnFieldDataChanged(sender, e);
        }

        private void Orgs_SelectedIndexChanged(object sender, EventArgs e)
        {
            FieldNames.Items.Clear();
            FieldRest fieldRest = m_sessionRest.GetFieldRest();
            FieldDefDto[] vecFields = fieldRest.GetFieldTypes(((SessionOrgInfoDto)Orgs.SelectedItem).Id);
            FieldDefDto field;
            for (int i = 0; i < vecFields.Length; ++i)
            {
                field = vecFields[i];
                if (field.Internal
                    || field.InputType != InputType.MultiSelect
                    && field.InputType != InputType.Select)
                {
                    continue;
                }

                FieldNames.Items.Add(field);
            }
        }

        private void BrowseBtn_Click(object sender, EventArgs e)
        {
            OpenFileDialog dlg = new OpenFileDialog();
            dlg.ShowDialog();
            ValuesFile.Text = dlg.FileName;
            OnFieldDataChanged(sender, e);
        }

        private void OnFieldDataChanged(object sender, EventArgs e)
        {
            SaveBtn.Enabled = Orgs.Items.Count > 0 && FieldNames.Items.Count > 0
                && FieldNames.SelectedIndex >= 0
                && !string.IsNullOrEmpty(ValuesFile.Text);
        }

        private void SaveBtn_Click(object sender, EventArgs e)
        {
            if (!File.Exists(ValuesFile.Text))
            {
                MessageBox.Show("\"" + ValuesFile.Text + "\" does not exist");
                return;
            }

            string[] vecLines = null;

            try
            {
                vecLines = File.ReadAllLines(ValuesFile.Text);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error reading file: " + ex.Message);
                return;
            }

            if (vecLines == null || vecLines.Length == 0)
            {
                MessageBox.Show("File contains no data");
                return;
            }

            FieldDefDto field = (FieldDefDto)FieldNames.SelectedItem;
            SortedList<string, FieldDefValueDto> mapExistingValues
                = new SortedList<string, FieldDefValueDto>();

            // cache existing values for faster lookup
            for (int i = 0; i < field.Values.Count; ++i)
            {
                mapExistingValues.Add(field.Values[i].Label.ToLower(),
                    field.Values[i]);
            }

            string strValue;
            FieldDefValueDto value;
            for (int i = 0; i < vecLines.Length; ++i)
            {
                strValue = vecLines[i];
                if (!string.IsNullOrEmpty(strValue)
                    && !string.IsNullOrEmpty(strValue = strValue.Trim())
                    && !mapExistingValues.ContainsKey(strValue.ToLower()))
                {
                    value = new FieldDefValueDto() { Label = strValue };
                    field.Values.Add(value);
                }
            }

            // we added values, save them
            if (field.Values.Count == mapExistingValues.Count)
            {
                MessageBox.Show("Data file contains no new field values");
                return;
            }

            try
            {
                FieldRest fieldRest = m_sessionRest.GetFieldRest();
                FieldDefDto savedField
                    = fieldRest.SaveField(((SessionOrgInfoDto)Orgs.SelectedItem).Id, field);

                if (savedField.Id == field.Id)
                {
                    // save the updated field back to the dropdown list so that
                    // it would contain the new values
                    FieldNames.Items[FieldNames.SelectedIndex] = savedField;

                    MessageBox.Show("Added new values to field \"" + field.Name + "\"");
                    return;
                }

                MessageBox.Show("Failed to save field values");
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
                return;
            }
        }

    }
}
