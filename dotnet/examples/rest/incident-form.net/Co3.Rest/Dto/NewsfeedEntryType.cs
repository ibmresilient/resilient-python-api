namespace Co3.Rest.Dto
{
    public enum NewsfeedEntryType
    {
        /// <summary>
        /// The object was created. 
        /// </summary>
        Create = 0,
        /// <summary>
        /// The status of the object changed.
        /// </summary>
        StatusChange = 1,
        /// <summary>
        /// The object was assigned to someone new.
        /// </summary>
        Assigned = 2,
        /// <summary>
        /// The object was removed.
        /// </summary>
        Removed = 3,
        /// <summary>
        /// The object had members removed.
        /// </summary>
        MembersRemoved = 4,
        /// <summary>
        /// The object had members added.
        /// </summary>
        MembersAdded = 5,
        /// <summary>
        /// The members list was set.
        /// </summary>
        MembersSet = 6,
        /// <summary>
        /// The members list was unset.
        /// </summary>
        MembersUnset = 7,
        /// <summary>
        /// The object was modified.
        /// </summary>
        Modify = 8,
        /// <summary>
        /// A comment was added to the object.
        /// </summary>
        CommentAdded = 9,
        /// <summary>
        /// A comment was removed from the object.
        /// </summary>
        CommentRemoved = 15,
        /// <summary>
        /// A comment was modified.
        /// </summary>
        CommentModified = 16,
        /// <summary>
        /// An attachment was added to the object.
        /// </summary>
        AttachmentAdded = 10,
        /// <summary>
        /// An attachment was removed from the object.
        /// </summary>
        AttachmentRemoved = 11,
        /// <summary>
        /// The system task summary was updated. This happens when the system automatically changes the task list because of rules.
        /// </summary>
        SystemTaskSummary = 12,
        /// <summary>
        /// Internal use only.
        /// </summary>
        Imported = 13,
        /// <summary>
        /// The incident's phase changed.
        /// </summary>
        PhaseChange = 14,
        /// <summary>
        /// A row was added to a datatable
        /// </summary>
        RowAdded = 17,
        /// <summary>
        /// A row was modified to a datatable
        /// </summary>
        RowModified = 18,
        /// <summary>
        /// A row was deleted to a datatable
        /// </summary>
        RowDeleted = 19
    }
}
